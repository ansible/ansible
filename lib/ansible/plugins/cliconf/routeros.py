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

DOCUMENTATION = """
---
cliconf: routeros
short_description: Use routeros cliconf to run command on MikroTik RouterOS platform
description:
  - This routeros plugin provides low level abstraction apis for
    sending and receiving CLI commands from MikroTik RouterOS network devices.
version_added: "2.7"
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
        device_info['network_os'] = 'RouterOS'

        resource = self.get('/system resource print')
        data = to_text(resource, errors='surrogate_or_strict').strip()
        match = re.search(r'version: (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        routerboard = self.get('/system routerboard print')
        data = to_text(routerboard, errors='surrogate_or_strict').strip()
        match = re.search(r'model: (.+)$', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        identity = self.get('/system identity print')
        data = to_text(identity, errors='surrogate_or_strict').strip()
        match = re.search(r'name: (.+)$', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_config(self, source='running', format='text', flags=None):
        return

    def edit_config(self, command):
        return

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
