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
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'vyos'
        reply = self.get(b'show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version:\s*(\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'HW model:\s*(\S+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get(b'show host name')
        device_info['network_os_hostname'] = to_text(reply, errors='surrogate_or_strict').strip()

        return device_info

    def get_config(self):
        return self.send_command(b'show configuration commands')

    def edit_config(self, command):
        for cmd in chain(['configure'], to_list(command)):
            self.send_command(to_bytes(cmd))

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def commit(self, comment=None):
        if comment:
            command = 'commit comment "{0}"'.format(comment)
        else:
            command = 'commit'
        self.send_command(to_bytes(command))

    def discard_changes(self, *args, **kwargs):
        self.send_command(b'discard')

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
