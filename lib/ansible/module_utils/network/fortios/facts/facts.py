from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

"""
The facts class for fortios
this file validates each subset of monitor and selectively
calls the appropriate facts gathering and monitoring function
"""

from ansible.module_utils.network.fortios.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.fortios.argspec.system.system import SystemArgs
from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.fortios.facts.system.system import SystemFacts


class Facts(FactsBase):
    """ The facts class for fortios
    """

    FACT_SUBSETS = {
        "system": SystemFacts
    }

    def __init__(self, module, fos=None, subset=None):
        super(Facts, self).__init__(module)
        self._fos = fos
        self._subset = subset

    def gen_runable(self, subsets, valid_subsets):
        """ Generate the runable subset

        :param module: The module instance
        :param subsets: The provided subsets
        :param valid_subsets: The valid subsets
        :rtype: list
        :returns: The runable subsets
        """
        runable_subsets = []
        FACT_DETAIL_SUBSETS = []
        FACT_DETAIL_SUBSETS.extend(SystemArgs.FACT_SYSTEM_SUBSETS)

        for subset in subsets:
            if subset['fact'] not in FACT_DETAIL_SUBSETS:
                self._module.fail_json(msg='Subset must be one of [%s], got %s' %
                                           (', '.join(sorted([item for item in FACT_DETAIL_SUBSETS])), subset['fact']))

            for valid_subset in frozenset(self.FACT_SUBSETS.keys()):
                if subset['fact'].startswith(valid_subset):
                    runable_subsets.append((subset, valid_subset))

        return runable_subsets

    def get_network_legacy_facts(self, fact_legacy_obj_map, legacy_facts_type=None):
        if not legacy_facts_type:
            legacy_facts_type = self._gather_subset

        runable_subsets = self.gen_runable(legacy_facts_type, frozenset(fact_legacy_obj_map.keys()))
        if runable_subsets:
            self.ansible_facts['ansible_net_gather_subset'] = []

            instances = list()
            for (subset, valid_subset) in runable_subsets:
                instances.append(fact_legacy_obj_map[valid_subset](self._module, self._fos, subset))

            for inst in instances:
                inst.populate_facts(self._connection, self.ansible_facts)

    def get_facts(self, facts_type=None, data=None):
        """ Collect the facts for fortios
        :param facts_type: List of facts types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        self.get_network_legacy_facts(self.FACT_SUBSETS, facts_type)

        return self.ansible_facts, self._warnings
