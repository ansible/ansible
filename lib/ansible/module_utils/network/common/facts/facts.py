#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts base class
this contains methods common to all facts subsets
"""

from ansible.module_utils.facts.collector import get_collector_names
from ansible.module_utils.network.common.network import get_resource_connection
from ansible.module_utils.six import iteritems


class FactsBase(object):
    """
    The facts base class
    """
    def __init__(self, module):
        self._module = module
        self._warnings = []
        self._gather_subset = module.params.get('gather_subset')
        self._gather_network_resources = module.params.get('gather_network_resources')
        self._connection = get_resource_connection(module)

        self.ansible_facts = {'ansible_network_resources': {}}
        self.ansible_facts['ansible_net_gather_network_resources'] = list()
        self.ansible_facts['ansible_net_gather_subset'] = list()

        if not self._gather_subset:
            self._gather_subset = ['!config']
        if not self._gather_network_resources:
            self._gather_network_resources = ['!all']

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

            restorun_subsets = get_collector_names(valid_subsets=net_res_choices,
                                                   gather_subset=resource_facts_type)
            if restorun_subsets:
                self.ansible_facts['ansible_net_gather_network_resources'] = list(restorun_subsets)
                instances = list()
                for key in restorun_subsets:
                    fact_cls_obj = facts_resource_obj_map.get(key)
                    if fact_cls_obj:
                        instances.append(fact_cls_obj(self._module))
                    else:
                        self._warnings.extend(["network resource fact gathering for '%s' is not supported" % key])

                for inst in instances:
                    inst.populate_facts(self._connection, self.ansible_facts, data)

    def get_network_legacy_facts(self, fact_legacy_obj_map, legacy_facts_type=None):
        if not legacy_facts_type:
            legacy_facts_type = self._gather_subset

        runable_subsets = get_collector_names(valid_subsets=frozenset(fact_legacy_obj_map.keys()),
                                              minimal_gather_subset=frozenset(['default']),
                                              gather_subset=legacy_facts_type)
        if runable_subsets:
            facts = dict()
            self.ansible_facts['ansible_net_gather_subset'] = list(runable_subsets)

            instances = list()
            for key in runable_subsets:
                instances.append(fact_legacy_obj_map[key](self._module))

            for inst in instances:
                inst.populate()
                facts.update(inst.facts)
                self._warnings.extend(inst.warnings)

            for key, value in iteritems(facts):
                key = 'ansible_net_%s' % key
                self.ansible_facts[key] = value
