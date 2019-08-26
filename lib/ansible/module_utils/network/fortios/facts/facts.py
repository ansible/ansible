#!/usr/bin/python
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
The monitor class for fortios
this file validates each subset of monitor and selectively
calls the appropriate monitoring function
"""

from ansible.module_utils.network.fortios.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.fortios.facts.system.system import SystemFacts


FACT_RESOURCE_SUBSETS = {
    "system": SystemFacts
}


class Facts(FactsBase):
    """ The fact class for fortios
    """

    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module, fos=None, uri=None):
        super(Facts, self).__init__(module)
        self._fos = fos
        self._uri = uri

    def gen_runable(self, subsets, valid_subsets):
        """ Generate the runable subset

        :param module: The module instance
        :param subsets: The provided subsets
        :param valid_subsets: The valid subsets
        :rtype: list
        :returns: The runable subsets
        """
        runable_subsets = set()

        for subset in subsets:
            if subset not in valid_subsets:
                self._module.fail_json(msg='Subset must be one of [%s], got %s' %
                                           (', '.join(sorted([item for item in valid_subsets])), subset))

            for valid_subset in self.VALID_RESOURCE_SUBSETS:
                if subset.startswith(valid_subset):
                    runable_subsets.add((subset, valid_subset))

        return runable_subsets

    def get_network_resources_facts(self, net_res_choices, facts_resource_obj_map, resource_facts_type=None, data=None):
        """
        :param net_res_choices:
        :param fact_resource_subsets:
        :param data: previously collected configuration
        :return:
        """
        if net_res_choices:
            if 'all' in net_res_choices:
                net_res_choices.remove('all')

        if net_res_choices:
            if not resource_facts_type:
                resource_facts_type = self._gather_subset

            restorun_subsets = self.gen_runable(resource_facts_type, frozenset(net_res_choices))
            if restorun_subsets:
                self.ansible_facts['ansible_net_gather_subset'] = list(restorun_subsets)
                instances = list()
                for (subset, valid_subset) in restorun_subsets:
                    fact_cls_obj = facts_resource_obj_map.get(valid_subset)
                    if fact_cls_obj:
                        instances.append(fact_cls_obj(self._module, self._fos, subset))
                    else:
                        self._warnings.extend(["network resource fact gathering for '%s' is not supported" % subset])

                for inst in instances:
                    inst.populate_facts(self._connection, self.ansible_facts, data)

    def get_facts(self, facts_type=None, data=None):
        """ Collect the facts for fortios
        :param facts_type: List of facts types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        netres_choices = FactsArgs.argument_spec['gather_subset'].get('choices', [])
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(netres_choices, FACT_RESOURCE_SUBSETS, facts_type, data)

        return self.ansible_facts, self._warnings
