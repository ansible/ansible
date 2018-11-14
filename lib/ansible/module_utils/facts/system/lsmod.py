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

import os
from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils.facts.collector import BaseFactCollector


class LsmodFactCollector(BaseFactCollector):
    name = 'lsmod'
    _fact_ids = set()

    def _get_proc_modules(self):
        if os.path.exists("/proc/modules") and os.access('/proc/modules', os.R_OK):
            return get_file_lines('/proc/modules')

    def _parse_proc_modules(self, modules):
        loaded_kernel_modules = []
        for mod in modules:
            module_dict = {}
            data = mod.split(" ", 5)
            module_dict['name'] = data[0]
            module_dict['size'] = data[1]
            module_dict['instances'] = data[2]
            if data[3] != "-":
                module_dict['dependencies'] = data[3].rstrip(',')
            else:
                module_dict['dependencies'] = ""
            module_dict['state'] = data[4]
            loaded_kernel_modules.append(module_dict)
        return loaded_kernel_modules

    def collect(self, module=None, collected_facts=None):
        lsmod_facts = {}
        modules = self._get_proc_modules()

        if not modules:
            return lsmod_facts

        lsmod_facts['loaded_kernel_modules'] = self._parse_proc_modules(modules)
        return lsmod_facts
