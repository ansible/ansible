# Collect facts related to LSB (Linux Standard Base)
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils.facts.collector import BaseFactCollector


class LSBFactCollector(BaseFactCollector):
    name = 'lsb'
    _fact_ids = set()

    def _lsb_release_bin(self, lsb_path, module):
        lsb_facts = {}

        if not lsb_path:
            return lsb_facts

        rc, out, err = module.run_command([lsb_path, "-a"], errors='surrogate_then_replace')
        if rc != 0:
            return lsb_facts

        for line in out.splitlines():
            if len(line) < 1 or ':' not in line:
                continue
            value = line.split(':', 1)[1].strip()

            if 'LSB Version:' in line:
                lsb_facts['release'] = value
            elif 'Distributor ID:' in line:
                lsb_facts['id'] = value
            elif 'Description:' in line:
                lsb_facts['description'] = value
            elif 'Release:' in line:
                lsb_facts['release'] = value
            elif 'Codename:' in line:
                lsb_facts['codename'] = value

        return lsb_facts

    def _lsb_release_file(self, etc_lsb_release_location):
        lsb_facts = {}

        if not os.path.exists(etc_lsb_release_location):
            return lsb_facts

        for line in get_file_lines(etc_lsb_release_location):
            value = line.split('=', 1)[1].strip()

            if 'DISTRIB_ID' in line:
                lsb_facts['id'] = value
            elif 'DISTRIB_RELEASE' in line:
                lsb_facts['release'] = value
            elif 'DISTRIB_DESCRIPTION' in line:
                lsb_facts['description'] = value
            elif 'DISTRIB_CODENAME' in line:
                lsb_facts['codename'] = value

        return lsb_facts

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        lsb_facts = {}

        if not module:
            return facts_dict

        lsb_path = module.get_bin_path('lsb_release')

        # try the 'lsb_release' script first
        if lsb_path:
            lsb_facts = self._lsb_release_bin(lsb_path,
                                              module=module)

        # no lsb_release, try looking in /etc/lsb-release
        if not lsb_facts:
            lsb_facts = self._lsb_release_file('/etc/lsb-release')

        if lsb_facts and 'release' in lsb_facts:
            lsb_facts['major_release'] = lsb_facts['release'].split('.')[0]

        facts_dict['lsb'] = lsb_facts
        return facts_dict
