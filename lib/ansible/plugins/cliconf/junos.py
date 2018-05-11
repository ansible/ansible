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

import json
import re
from itertools import chain

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'junos'

        reply = self.get(command='show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Junos: (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'Model: (\S+)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'Hostname: (\S+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)
        return device_info

    def get_config(self, source='running', format='text'):
        if source != 'running':
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        if format == 'text':
            cmd = 'show configuration'
        else:
            cmd = 'show configuration | display %s' % format
        return self.send_command(cmd)

    def edit_config(self, command):
        for cmd in chain(['configure'], to_list(command)):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def commit(self, *args, **kwargs):
        """Execute commit command on remote device.
        :kwargs:
            comment: Optional commit description.
        """
        comment = kwargs.get('comment', None)
        command = 'commit'
        if comment:
            command += ' comment {0}'.format(comment)
        command += ' and-quit'
        return self.send_command(command)

    def discard_changes(self):
        command = 'rollback 0'
        for cmd in chain(to_list(command), 'exit'):
            self.send_command(cmd)

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)

    def compare_configuration(self, rollback_id=None):
        command = 'show | compare'
        if rollback_id is not None:
            command += ' rollback %s' % int(rollback_id)
        return self.send_command(command)
