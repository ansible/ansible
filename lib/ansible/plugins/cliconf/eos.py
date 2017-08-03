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
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'eos'
        reply = self.get(b'show version | json')
        data = json.loads(reply)

        device_info['network_os_version'] = data['version']
        device_info['network_os_model'] = data['modelName']

        reply = self.get(b'show hostname | json')
        data = json.loads(reply)

        device_info['network_os_hostname'] = data['hostname']

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text'):
        lookup = {'running': 'running-config', 'startup': 'startup-config'}
        if source not in lookup:
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        if format == 'text':
            cmd = b'show %s' % lookup[source]
        else:
            cmd = b'show %s | %s' % (lookup[source], format)
        return self.send_command(cmd)

    @enable_mode
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
