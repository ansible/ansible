#
# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re

from ansible.module_utils._text import to_text, to_native
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_connected, ensure_ncclient

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml, new_ele, sub_ele
    HAS_NCCLIENT = True
except (ImportError, AttributeError):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False


class Netconf(NetconfBase):
    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    @ensure_ncclient
    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'junos'
        ele = new_ele('get-software-information')
        data = self.execute_rpc(to_xml(ele))
        reply = to_ele(data)
        sw_info = reply.find('.//software-information')

        device_info['network_os_version'] = self.get_text(sw_info, 'junos-version')
        device_info['network_os_hostname'] = self.get_text(sw_info, 'host-name')
        device_info['network_os_model'] = self.get_text(sw_info, 'product-model')

        return device_info

    @ensure_connected
    def execute_rpc(self, name):
        """
        RPC to be execute on remote device
        :param name: Name of rpc in string format
        :return: Received rpc response from remote host
        """
        return self.rpc(name)

    @ensure_ncclient
    @ensure_connected
    def load_configuration(self, format='xml', action='merge', target='candidate', config=None):
        """
        Load given configuration on device
        :param format: Format of configuration (xml, text, set)
        :param action: Action to be performed (merge, replace, override, update)
        :param target: The name of the configuration datastore being edited
        :param config: The configuration to be loaded on remote host in string format
        :return: Received rpc response from remote host in string format
        """
        if config:
            if format == 'xml':
                config = to_ele(config)

        try:
            return self.m.load_configuration(format=format, action=action, target=target, config=config).data_xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes', 'validate', 'lock', 'unlock', 'copy_copy',
                                               'execute_rpc', 'load_configuration', 'get_configuration', 'command',
                                               'reboot', 'halt']
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        result['device_operations'] = self.get_device_operations(result['server_capabilities'])
        return json.dumps(result)

    @staticmethod
    @ensure_ncclient
    def guess_network_os(obj):
        """
        Guess the remote network os name
        :param obj: Netconf connection class object
        :return: Network OS name
        """
        try:
            m = manager.connect(
                host=obj._play_context.remote_addr,
                port=obj._play_context.port or 830,
                username=obj._play_context.remote_user,
                password=obj._play_context.password,
                key_filename=obj.key_filename,
                hostkey_verify=obj.get_option('host_key_checking'),
                look_for_keys=obj.get_option('look_for_keys'),
                allow_agent=obj._play_context.allow_agent,
                timeout=obj.get_option('persistent_connect_timeout')
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(to_native(exc))

        guessed_os = None
        for c in m.server_capabilities:
            if re.search('junos', c):
                guessed_os = 'junos'

        m.close_session()
        return guessed_os

    @ensure_connected
    def get_configuration(self, format='xml', filter=None):
        """
        Retrieve all or part of a specified configuration.
        :param format: format in which configuration should be retrieved
        :param filter: specifies the portion of the configuration to retrieve
        :return: Received rpc response from remote host in string format
        """
        return self.m.get_configuration(format=format, filter=filter).data_xml

    @ensure_connected
    def compare_configuration(self, rollback=0):
        """
        Compare the candidate configuration with running configuration
        by default. The candidate configuration can be compared with older
        committed configuration by providing rollback id.
        :param rollback: Rollback id of previously commited configuration
        :return: Received rpc response from remote host in string format
        """
        return self.m.compare_configuration(rollback=rollback).data_xml

    @ensure_connected
    def halt(self):
        """reboot the device"""
        return self.m.halt().data_xml

    @ensure_connected
    def reboot(self):
        """reboot the device"""
        return self.m.reboot().data_xml

    # Due to issue in ncclient commit() method for Juniper (https://github.com/ncclient/ncclient/issues/238)
    # below commit() is a workaround which build's raw `commit-configuration` xml with required tags and uses
    # ncclient generic rpc() method to execute rpc on remote host.
    # Remove below method after the issue in ncclient is fixed.
    @ensure_ncclient
    @ensure_connected
    def commit(self, confirmed=False, check=False, timeout=None, comment=None, synchronize=False, at_time=None):
        """
        Commit the candidate configuration as the device's new current configuration.
        Depends on the `:candidate` capability.
        A confirmed commit (i.e. if *confirmed* is `True`) is reverted if there is no
        followup commit within the *timeout* interval. If no timeout is specified the
        confirm timeout defaults to 600 seconds (10 minutes).
        A confirming commit may have the *confirmed* parameter but this is not required.
        Depends on the `:confirmed-commit` capability.
        :param confirmed: whether this is a confirmed commit
        :param check: Check correctness of syntax
        :param timeout: specifies the confirm timeout in seconds
        :param comment: Message to write to commit log
        :param synchronize: Synchronize commit on remote peers
        :param at_time: Time at which to activate configuration changes
        :return: Received rpc response from remote host
        """
        obj = new_ele('commit-configuration')
        if confirmed:
            sub_ele(obj, 'confirmed')
        if check:
            sub_ele(obj, 'check')
        if synchronize:
            sub_ele(obj, 'synchronize')
        if at_time:
            subele = sub_ele(obj, 'at-time')
            subele.text = str(at_time)
        if comment:
            subele = sub_ele(obj, 'log')
            subele.text = str(comment)
        if timeout:
            subele = sub_ele(obj, 'confirm-timeout')
            subele.text = str(timeout)
        return self.rpc(obj)
