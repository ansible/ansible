#
# (c) 2018 Red Hat Inc.
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
cliconf: edgeswitch
short_description: Use edgeswitch cliconf to run command on EdgeSwitch platform
description:
  - This edgeswitch plugin provides low level abstraction apis for
    sending and receiving CLI commands from Ubiquiti EdgeSwitch network devices.
version_added: "2.8"
"""

import re
import time
import json

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.config import dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible.module_utils.common._collections_compat import Mapping


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'edgeswitch'
        reply = self.get(command='show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Software Version\.+ (.*)', data)
        if match:
            device_info['network_os_version'] = match.group(1).strip(',')

        match = re.search(r'^Machine Model\.+ (.*)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'System Name\.+ (.*)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', flags=None):
        if source not in ('running', 'startup'):
            raise ValueError("fetching configuration from %s is not supported" % source)

        if source == 'running':
            cmd = 'show running-config '
        else:
            cmd = 'show startup-config '

        if flags:
            cmd += ' '.join(to_list(flags))
            cmd = cmd.strip()

        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, commands):
        resp = {}

        results = []
        requests = []
        self.send_command('configure')
        for line in to_list(commands):
            if not isinstance(line, Mapping):
                line = {'command': line}

            cmd = line['command']
            if cmd != 'end' and cmd[0] != '!':
                results.append(self.send_command(**line))
                requests.append(cmd)

        self.send_command('end')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command=None, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if not command:
            raise ValueError('must provide value of command to execute')
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['run_commands']
        return json.dumps(result)

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                raise ValueError("'output' value %s is not supported for run_commands" % output)

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', e)

            responses.append(out)

        return responses
