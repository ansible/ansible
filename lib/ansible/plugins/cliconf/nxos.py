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

from ansible.module_utils.network_common import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'nxos'
        reply = self.get(b'show version | json')
        data = json.loads(reply)

        device_info['network_os_version'] = data['sys_ver_str']
        device_info['network_os_model'] = data['chassis_id']
        device_info['network_os_hostname'] = data['host_name']
        device_info['network_os_image'] = data['isan_file_name']

        return device_info

    def get_config(self, source='running'):
        lookup = {'running': 'running-config', 'startup': 'startup-config'}
        return self.send_command(b'show %s' % lookup[source])

    def edit_config(self, command):
        for cmd in chain([b'configure'], to_list(command), [b'end']):
            self.send_command(cmd)

    def get(self, *args, **kwargs):
        return self.send_command(*args, **kwargs)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
