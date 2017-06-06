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
from xml.etree.ElementTree import fromstring

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network_common import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'junos'
        reply = self.get(b'show version | display xml')
        data = fromstring(to_text(reply, errors='surrogate_then_replace').strip())

        sw_info = data.find('.//software-information')

        device_info['network_os_version'] = self.get_text(sw_info, 'junos-version')
        device_info['network_os_hostname'] = self.get_text(sw_info, 'host-name')
        device_info['network_os_model'] = self.get_text(sw_info, 'product-model')

        return device_info

    def get_config(self, source='running', format='text'):
        if source != 'running':
            return self.invalid_params("fetching configuration from %s is not supported" % source)
        if format == 'text':
            cmd = b'show configuration'
        else:
            cmd = b'show configuration | display %s' % format
        return self.send_command(to_bytes(cmd), errors='surrogate_or_strict')

    def edit_config(self, command):
        for cmd in chain([b'configure'], to_list(command)):
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
        self.send_command(b'rollback')

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)
