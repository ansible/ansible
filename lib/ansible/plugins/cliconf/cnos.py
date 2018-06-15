# (C) 2017 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
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
# Contains CLIConf Plugin methods for CNOS Modules
# Lenovo Networking
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

        device_info['network_os'] = 'cnos'
        reply = self.get(b'display version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'^System version: (.*?) ', data, re.M | re.I)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'^Lenovo RackSwitch (\S+)', data, re.M | re.I)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'^Device name: (.*?) ', data, re.M | re.I)
        if match:
            device_info['network_os_hostname'] = match.group(1)
        else:
            device_info['network_os_hostname'] = "NA"

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text'):
        if source not in ('running', 'startup'):
            msg = "fetching configuration from %s is not supported"
            return self.invalid_params(msg % source)
        if source == 'running':
            cmd = b'display running-config'
        else:
            cmd = b'display startup-config'
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        for cmd in chain([b'configure device'], to_list(command), [b'end']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
