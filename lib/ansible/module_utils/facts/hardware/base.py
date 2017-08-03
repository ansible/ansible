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

from ansible.module_utils.facts.collector import BaseFactCollector


class Hardware:
    platform = 'Generic'

    # FIXME: remove load_on_init when we can
    def __init__(self, module, load_on_init=False):
        self.module = module

    def populate(self, collected_facts=None):
        return {}


class HardwareCollector(BaseFactCollector):
    name = 'hardware'
    _fact_ids = set(['processor',
                     'processor_cores',
                     'processor_count',
                     # TODO: mounts isnt exactly hardware
                     'mounts',
                     'devices'])
    _fact_class = Hardware

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}
        if not module:
            return {}

        # Network munges cached_facts by side effect, so give it a copy
        facts_obj = self._fact_class(module)

        facts_dict = facts_obj.populate(collected_facts=collected_facts)

        return facts_dict
