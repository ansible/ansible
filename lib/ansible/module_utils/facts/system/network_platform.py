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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import platform

from ansible.module_utils.facts.collector import BaseFactCollector

from ansible.module_utils.connection import Connection


class NetworkFactCollector(BaseFactCollector):
    name = 'network_platform'

    _fact_ids = set(['system',
                     'kernel',
                     'machine',
                     'python_version',
                     'architecture',
                     'machine_id'])

    def collect(self, module=None, collected_facts=None):

        platform_facts = {}

        self.connection = Connection(module._socket_path)
        capabilities = module.from_json(self.connection.get_capabilities())

        # platform_facts['network_capabilities'] = capabilities

        capabilities.pop('network_os')
        platform_facts.update(capabilities['device_info'])

        platform_facts['system'] = capabilities['device_info']['network_os']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts
