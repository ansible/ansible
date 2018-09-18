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

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        reply = self.get(b'show version | json-print')
        data = json.loads(reply)
        device_info['network_os'] = data['Product name']
        device_info['network_os_version'] = data['Version summary']
        device_info['network_os_model'] = data['Product model']

        reply = self.get(b'show version | include Hostname')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        hostname = data.split(':')[1]
        hostname = hostname.strip()
        device_info['network_os_hostname'] = hostname

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text'):
        if source not in ('running',):
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        cmd = b'show running-config'
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        for cmd in chain([b'configure terminal'], to_list(command), [b'exit']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
