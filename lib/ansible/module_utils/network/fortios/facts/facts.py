#
# -*- coding: utf-8 -*-
# Copyright 2019 Fortinet, Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The monitor class for fortios
this file validates each subset of monitor and selectively
calls the appropriate monitoring function
"""

from ansible.module_utils.network.fortios.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.fortios.facts.system.system import SystemFacts
from ansible.module_utils.network.fortios.facts.firewall.firewall import FirewallFacts


FACT_RESOURCE_SUBSETS = {
    "firewall": FirewallFacts,
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
                resource_facts_type = self._gather_network_resources

            restorun_subsets = self.gen_runable(resource_facts_type, frozenset(net_res_choices))
            if restorun_subsets:
                self.ansible_facts['ansible_net_gather_network_resources'] = list(restorun_subsets)
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
        netres_choices = FactsArgs.argument_spec['gather_network_resources'].get('choices', [])
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(netres_choices, FACT_RESOURCE_SUBSETS, facts_type, data)

        return self.ansible_facts, self._warnings
