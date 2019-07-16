# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
cliconf: edgeos
short_description: Use edgeos cliconf to run command on EdgeOS platform
description:
  - This edgeos plugin provides low level abstraction apis for
    sending and receiving CLI commands from Ubiquiti EdgeOS network devices.
version_added: "2.5"
"""

import re
import json

from itertools import chain

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'edgeos'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version:\s*v?(\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'HW model:\s*(\S+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get('show host name')
        reply = to_text(reply, errors='surrogate_or_strict').strip()
        device_info['network_os_hostname'] = reply

        return device_info

    def get_config(self, source='running', format='text', flags=None):
        return self.send_command('show configuration commands')

    def edit_config(self, candidate=None, commit=True, replace=False, comment=None):
        for cmd in chain(['configure'], to_list(candidate)):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def commit(self, comment=None):
        if comment:
            command = 'commit comment "{0}"'.format(comment)
        else:
            command = 'commit'
        self.send_command(command)

    def discard_changes(self, *args, **kwargs):
        self.send_command('discard')

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['commit', 'discard_changes']
        return json.dumps(result)
