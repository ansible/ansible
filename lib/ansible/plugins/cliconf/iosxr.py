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
from ansible.module_utils.network_common import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'iosxr'
        reply = self.get(b'show version brief')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version (\S+)$', data, re.M)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'image file is "(.+)"', data)
        if match:
            device_info['network_os_image'] = match.group(1)

        match = re.search(r'^Cisco (.+) \(revision', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'^(.+) uptime', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_config(self, source='running'):
        lookup = {'running': 'running-config'}
        if source not in lookup:
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        return self.send_command(to_bytes(b'show %s' % lookup[source], errors='surrogate_or_strict'))

    def edit_config(self, command):
        for cmd in chain([b'configure'], to_list(command), [b'end']):
            self.send_command(cmd)

    def get(self, *args, **kwargs):
        return self.send_command(*args, **kwargs)

    def commit(self, comment=None):
        if comment:
            command = b'commit comment {0}'.format(comment)
        else:
            command = b'commit'
        self.send_command(command)

    def discard_changes(self):
        self.send_command(b'abort')

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
