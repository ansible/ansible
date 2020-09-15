#
# (c) 2017 Red Hat Inc.
#
# (c) 2017 Dell EMC.
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
cliconf: dellos6
short_description: Use dellos6 cliconf to run command on Dell OS6 platform
description:
  - This dellos6 plugin provides low level abstraction apis for
    sending and receiving CLI commands from Dell OS6 network devices.
version_added: 2.5
"""

import re
import json

from itertools import chain

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'dellos6'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Software Version (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'System Type (\S+)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get('show running-config | grep hostname')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'^hostname (.+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text', flags=None):
        if source not in ('running', 'startup'):
            return self.invalid_params("fetching configuration from %s is not supported" % source)
#        if source == 'running':
#            cmd = 'show running-config all'
        else:
            cmd = 'show startup-config'
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        for cmd in chain(['configure terminal'], to_list(command), ['end']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)

    def set_cli_prompt_context(self):
        """
        Make sure we are in the operational cli mode
        :return: None
        """
        if self._connection.connected:
            self._update_cli_prompt_context(config_context=')#')
