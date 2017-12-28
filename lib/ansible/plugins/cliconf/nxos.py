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

from itertools import chain

from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'nxos'
        reply = self.get(b'show version | json')
        data = json.loads(reply)
        platform_reply = self.get(b'show inventory | json')
        platform_info = json.loads(platform_reply)

        device_info['network_os_version'] = data.get('sys_ver_str') or data.get('kickstart_ver_str')
        device_info['network_os_model'] = data['chassis_id']
        device_info['network_os_hostname'] = data['host_name']
        device_info['network_os_image'] = data.get('isan_file_name') or data.get('kick_file_name')

        inventory_table = platform_info['TABLE_inv']['ROW_inv']
        for info in inventory_table:
            if 'Chassis' in info['name']:
                device_info['network_os_platform'] = info['productid']

        return device_info

    def get_config(self, source='running', flags=None):
        lookup = {'running': 'running-config', 'startup': 'startup-config'}

        cmd = b'show {} '.format(lookup[source])
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, command):
        responses = []
        for cmd in chain([b'configure'], to_list(command), [b'end']):
            responses.append(self.send_command(cmd))

        return json.dumps(responses)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
