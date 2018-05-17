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

from ansible import constants as C
from ansible.module_utils._text import to_text, to_bytes
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_connected

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml, new_ele
except ImportError:
    raise AnsibleError("ncclient is not installed")


class Netconf(NetconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

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
        """RPC to be execute on remote device
           :name: Name of rpc in string format"""
        return self.rpc(name)

    @ensure_connected
    def load_configuration(self, *args, **kwargs):
        """Loads given configuration on device
        :format: Format of configuration (xml, text, set)
        :action: Action to be performed (merge, replace, override, update)
        :target: is the name of the configuration datastore being edited
        :config: is the configuration in string format."""
        if kwargs.get('config'):
            kwargs['config'] = to_bytes(kwargs['config'], errors='surrogate_or_strict')
            if kwargs.get('format', 'xml') == 'xml':
                kwargs['config'] = to_ele(kwargs['config'])

        try:
            return self.m.load_configuration(*args, **kwargs).data_xml
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
    def guess_network_os(obj):

        try:
            m = manager.connect(
                host=obj._play_context.remote_addr,
                port=obj._play_context.port or 830,
                username=obj._play_context.remote_user,
                password=obj._play_context.password,
                key_filename=obj._play_context.private_key_file,
                hostkey_verify=C.HOST_KEY_CHECKING,
                look_for_keys=C.PARAMIKO_LOOK_FOR_KEYS,
                allow_agent=obj._play_context.allow_agent,
                timeout=obj._play_context.timeout
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(str(exc))

        guessed_os = None
        for c in m.server_capabilities:
            if re.search('junos', c):
                guessed_os = 'junos'

        m.close_session()
        return guessed_os

    @ensure_connected
    def get_configuration(self, *args, **kwargs):
        """Retrieve all or part of a specified configuration.
           :format: format in configuration should be retrieved
           :filter: specifies the portion of the configuration to retrieve
           (by default entire configuration is retrieved)"""
        return self.m.get_configuration(*args, **kwargs).data_xml

    @ensure_connected
    def compare_configuration(self, *args, **kwargs):
        """Compare configuration
           :rollback: rollback id"""
        return self.m.compare_configuration(*args, **kwargs).data_xml

    @ensure_connected
    def halt(self):
        """reboot the device"""
        return self.m.halt().data_xml

    @ensure_connected
    def reboot(self):
        """reboot the device"""
        return self.m.reboot().data_xml
