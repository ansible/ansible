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

from ansible.module_utils.six import iteritems

from ansible.module_utils.facts.collector import BaseFactCollector


class EnvFactCollector(BaseFactCollector):
    name = 'env'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        env_facts = {}
        env_facts['env'] = {}

        for k, v in iteritems(os.environ):
            env_facts['env'][k] = v

        return env_facts
