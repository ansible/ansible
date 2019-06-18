#
# (c) 2016 Red Hat Inc.
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
cliconf: netvisor
short_description: Use netvisor cliconf to run command on Pluribus netvisor platform
description:
  - This netvisor plugin provides low level abstraction apis for
    sending and receiving CLI commands from Pluribus netvisor devices.
version_added: 2.8
"""

import json
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_config(self, source='running', format='text', flags=None):
        if source not in ('running'):
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        cmd = 'show running-config'
        return self.send_command(cmd)

    def edit_config(self, command):
        return

    def get(self, command=None, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if not command:
            raise ValueError('must provide value of command to execute')
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block'],
            'output': []
        }

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        result.update(self.get_option_values())
        return json.dumps(result)

    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'netvisor'

        return device_info
