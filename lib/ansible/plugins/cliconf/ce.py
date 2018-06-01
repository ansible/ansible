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

import re
import json

from itertools import chain

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'ce'
        reply = self.get(b'display version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'^Huawei.+\n.+\Version\s+(\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1).strip(',')

        match = re.search(r'^Huawei(.+)\n.+\(\S+\s+\S+\)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'HUAWEI\s+(\S+)\s+uptime', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text', flags=None):
        if source not in ('running'):
            return self.invalid_params("fetching configuration from %s is not supported" % source)

        if not flags:
            flags = []

        cmd = 'display current-configuration'

        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        results = []
        for cmd in chain(['configure terminal'], to_list(command), ['end']):
            if isinstance(cmd, dict):
                command = cmd['command']
                prompt = cmd['prompt']
                answer = cmd['answer']
                newline = cmd.get('newline', True)
            else:
                command = cmd
                prompt = None
                answer = None
                newline = True

            results.append(self.send_command(command, prompt, answer, False, newline))
        return results[1:-1]

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
