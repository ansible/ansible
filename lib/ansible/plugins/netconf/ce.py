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

from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_connected, ensure_ncclient

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml, new_ele
    HAS_NCCLIENT = True
except (ImportError, AttributeError):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False

try:
    from lxml.etree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring


class Netconf(NetconfBase):

    @ensure_ncclient
    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    @ensure_ncclient
    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'ce'
        filter_xml = '''<filter type="subtree">
                          <system xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
                            <systemInfo>
                              <sysName></sysName>
                              <sysContact></sysContact>
                              <productVer></productVer>
                              <platformVer></platformVer>
                              <productName></productName>
                            </systemInfo>
                          </system>
                        </filter>'''
        data = self.get(filter_xml)
        data = re.sub(r'xmlns=".+?"', r'', data)
        reply = fromstring(to_bytes(data, errors='surrogate_or_strict'))
        sw_info = reply.find('.//systemInfo')

        device_info['network_os_version'] = self.get_text(sw_info, 'productVer')
        device_info['network_os_hostname'] = self.get_text(sw_info, 'sysName')
        device_info['network_os_platform_version'] = self.get_text(sw_info, 'platformVer')
        device_info['network_os_platform'] = self.get_text(sw_info, 'productName')

        return device_info

    @ensure_connected
    def execute_rpc(self, name):
        """RPC to be execute on remote device
           :name: Name of rpc in string format"""
        return self.rpc(name)

    @ensure_ncclient
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
        return json.dumps(result)

    @staticmethod
    @ensure_ncclient
    def guess_network_os(obj):
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
            if re.search('huawei', c):
                guessed_os = 'ce'
                break

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

    @ensure_ncclient
    @ensure_connected
    def execute_action(self, xml_str):
        """huawei execute-action"""
        con_obj = None
        try:
            con_obj = self.m.action(action=xml_str)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

        return con_obj.xml

    @ensure_connected
    def halt(self):
        """reboot the device"""
        return self.m.halt().data_xml

    @ensure_connected
    def reboot(self):
        """reboot the device"""
        return self.m.reboot().data_xml

    @ensure_ncclient
    @ensure_connected
    def get(self, *args, **kwargs):
        try:
            if_rpc_reply = kwargs.pop('if_rpc_reply', False)
            if if_rpc_reply:
                return self.m.get(*args, **kwargs).xml
            return self.m.get(*args, **kwargs).data_xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_ncclient
    @ensure_connected
    def get_config(self, *args, **kwargs):
        try:
            return self.m.get_config(*args, **kwargs).data_xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_ncclient
    @ensure_connected
    def edit_config(self, *args, **kwargs):
        try:
            return self.m.edit_config(*args, **kwargs).xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_ncclient
    @ensure_connected
    def execute_nc_cli(self, *args, **kwargs):
        try:
            return self.m.cli(*args, **kwargs).xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_ncclient
    @ensure_connected
    def commit(self, *args, **kwargs):
        try:
            return self.m.commit(*args, **kwargs).data_xml
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def validate(self, *args, **kwargs):
        return self.m.validate(*args, **kwargs).data_xml

    @ensure_connected
    def discard_changes(self, *args, **kwargs):
        return self.m.discard_changes(*args, **kwargs).data_xml

    @ensure_ncclient
    @ensure_connected
    def dispatch_rpc(self, rpc_command=None, source=None, filter=None):
        """
        Execute rpc on the remote device eg. dispatch('get-next')
        :param rpc_command: specifies rpc command to be dispatched either in plain text or in xml element format (depending on command)
        :param source: name of the configuration datastore being queried
        :param filter: specifies the portion of the configuration to retrieve (by default entire configuration is retrieved)
        :return: Returns xml string containing the rpc-reply response received from remote host
        """
        if rpc_command is None:
            raise ValueError('rpc_command value must be provided')
        resp = self.m.dispatch(fromstring(rpc_command), source=source, filter=filter)
        # just return rpc-reply xml
        return resp.xml
