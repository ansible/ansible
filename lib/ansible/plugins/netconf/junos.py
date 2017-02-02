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

from xml.etree.ElementTree import fromstring

from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_connected

from ncclient.xml_ import new_ele


class Netconf(NetconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'junos'
        data = self.execute_rpc('get-software-information')
        reply = fromstring(data)
        sw_info = reply.find('.//software-information')

        device_info['network_os_version'] = self.get_text(sw_info, 'junos-version')
        device_info['network_os_hostname'] = self.get_text(sw_info, 'host-name')
        device_info['network_os_model'] = self.get_text(sw_info, 'product-model')

        return device_info

    @ensure_connected
    def execute_rpc(self, rpc):
        """RPC to be execute on remote device
           :rpc: Name of rpc in string format"""
        name = new_ele(rpc)
        return self.m.rpc(name).data_xml

    @ensure_connected
    def load_configuration(self, *args, **kwargs):
        """Loads given configuration on device
        :format: Format of configuration (xml, text, set)
        :action: Action to be performed (merge, replace, override, update)
        :target: is the name of the configuration datastore being edited
        :config: is the configuration in string format."""
        return self.m.load_configuration(*args, **kwargs).data_xml

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes', 'validate', 'lock', 'unlock', 'copy_copy']
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        return json.dumps(result)
