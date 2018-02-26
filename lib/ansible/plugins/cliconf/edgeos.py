# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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

        device_info['network_os'] = 'edgeos'
        reply = self.get(b'show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version:\s*v?(\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'HW model:\s*(\S+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get(b'show host name')
        reply = to_text(reply, errors='surrogate_or_strict').strip()
        device_info['network_os_hostname'] = reply

        return device_info

    def get_config(self, source='running', format='text'):
        return self.send_command(b'show configuration commands')

    def edit_config(self, command):
        for cmd in chain([b'configure'], to_list(command)):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(to_bytes(command),
                                 prompt=to_bytes(prompt),
                                 answer=to_bytes(answer),
                                 sendonly=sendonly)

    def commit(self, comment=None):
        if comment:
            command = 'commit comment "{0}"'.format(comment)
        else:
            command = 'commit'
        self.send_command(command)

    def discard_changes(self, *args, **kwargs):
        self.send_command(b'discard')

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
