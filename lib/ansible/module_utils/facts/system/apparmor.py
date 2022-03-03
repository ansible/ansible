# Collect facts related to apparmor
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

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class ApparmorFactCollector(BaseFactCollector):
    name = 'apparmor'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        apparmor_facts = {}
        if os.path.exists('/sys/kernel/security/apparmor'):
            apparmor_facts['status'] = 'enabled'
        else:
            apparmor_facts['status'] = 'disabled'

        facts_dict['apparmor'] = apparmor_facts
        return facts_dict
