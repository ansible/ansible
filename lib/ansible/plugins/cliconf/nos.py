#
# (c) 2018 Extreme Networks Inc.
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

DOCUMENTATION = """
---
cliconf: nos
short_description: Use nos cliconf to run command on Extreme NOS platform
description:
  - This nos plugin provides low level abstraction apis for
    sending and receiving CLI commands from Extreme NOS network devices.
version_added: "2.7"
"""

import re
import json

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'nos'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Network Operating System Version: (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        reply = self.get('show chassis')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'^Chassis Name:(\s+)(\S+)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(2)

        reply = self.get('show running-config | inc "switch-attributes host-name"')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'switch-attributes host-name (\S+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_config(self, source='running', flags=None):
        if source not in 'running':
            raise ValueError("fetching configuration from %s is not supported" % source)
        if source == 'running':
            cmd = 'show running-config'

        flags = [] if flags is None else flags
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, command):
        resp = {}
        results = []
        requests = []
        self.send_command('configure terminal')
        for cmd in to_list(command):
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

            if cmd != 'end' and cmd[0] != '!':
                results.append(self.send_command(command, prompt, answer, False, newline))
                requests.append(cmd)

        self.send_command('end')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command, prompt=None, answer=None, sendonly=False, check_all=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
