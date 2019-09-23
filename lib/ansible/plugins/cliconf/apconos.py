# (C) 2018 Red Hat Inc.
# Copyright (C) 2019 APCON.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Contains CLIConf Plugin methods for apconos Modules
# APCON Networking

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: "David Li (@davidlee-ap)"
cliconf: apconos
short_description: Use apconos cliconf to run command on APCON network devices
description:
  - This apconos plugin provides low level abstraction apis for
    sending and receiving CLI commands from APCON network devices.
version_added: "2.9"
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

        device_info['network_os'] = 'apconos'
        reply = self.get(b'show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        if data:
            device_info['network_os_version'] = self.parse_version(data)
            device_info['network_os_model'] = self.parse_model(data)

        return device_info

    def parse_version(self, data):
        return ""

    def parse_model(self, data):
        return ""

    @enable_mode
    def get_config(self, source='running', format='text'):
        pass

    @enable_mode
    def edit_config(self, command):
        for cmd in chain([b'configure terminal'], to_list(command), [b'end']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, check_all=check_all)

    def get_capabilities(self):
        return json.dumps(self.get_device_info())
