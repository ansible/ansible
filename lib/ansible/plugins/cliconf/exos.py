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

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'exos'

        reply = self.get(b'show switch detail')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'ExtremeXOS version  (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'System Type: +(\S+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'SysName: +(\S+)', data)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_config(self, source='running', flags=None):
        if source not in ('running', 'startup'):
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        if source == 'running':
            cmd = 'show configuration'
        else:
            cmd = 'debug cfgmgr show configuration file'
            reply = self.get(b'show switch | include "Config Selected"')
            data = to_text(reply, errors='surrogate_or_strict').strip()
            match = re.search(r': +(\S+)\.cfg', data)
            if match:
                cmd += ' '.join(match.group(1))
                cmd = cmd.strip()

        flags = [] if flags is None else flags
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, command):
        for cmd in chain(to_list(command)):
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
            self.send_command(to_bytes(command), to_bytes(prompt), to_bytes(answer),
                              False, newline)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
