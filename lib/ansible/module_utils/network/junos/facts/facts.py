#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for junos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.junos.facts.legacy.base import Default, Hardware, Config, Interfaces, OFacts, HAS_PYEZ
from ansible.module_utils.network.junos.facts.interfaces.interfaces import InterfacesFacts
from ansible.module_utils.network.junos.facts.lacp.lacp import LacpFacts
from ansible.module_utils.network.junos.facts.lacp_interfaces.lacp_interfaces import Lacp_interfacesFacts
from ansible.module_utils.network.junos.facts.lag_interfaces.lag_interfaces import Lag_interfacesFacts
from ansible.module_utils.network.junos.facts.l3_interfaces.l3_interfaces import L3_interfacesFacts
from ansible.module_utils.network.junos.facts.lldp_global.lldp_global import Lldp_globalFacts
from ansible.module_utils.network.junos.facts.lldp_interfaces.lldp_interfaces import Lldp_interfacesFacts
from ansible.module_utils.network.junos.facts.vlans.vlans import VlansFacts
from ansible.module_utils.network.junos.facts.l2_interfaces.l2_interfaces import L2_interfacesFacts

FACT_LEGACY_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
    interfaces=Interfaces,
)
FACT_RESOURCE_SUBSETS = dict(
    interfaces=InterfacesFacts,
    lacp=LacpFacts,
    lacp_interfaces=Lacp_interfacesFacts,
    lag_interfaces=Lag_interfacesFacts,
    l2_interfaces=L2_interfacesFacts,
    l3_interfaces=L3_interfacesFacts,
    lldp_global=Lldp_globalFacts,
    lldp_interfaces=Lldp_interfacesFacts,
    vlans=VlansFacts,
)


class Facts(FactsBase):
    """ The fact class for junos
    """

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for junos
        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(FACT_RESOURCE_SUBSETS, resource_facts_type, data)

        if not legacy_facts_type:
            legacy_facts_type = self._gather_subset
            # fetch old style facts only when explicitly mentioned in gather_subset option
            if 'ofacts' in legacy_facts_type:
                if HAS_PYEZ:
                    self.ansible_facts.update(OFacts(self._module).populate())
                else:
                    self._warnings.extend([
                        'junos-eznc is required to gather old style facts but does not appear to be installed. '
                        'It can be installed using `pip  install junos-eznc`'])
                self.ansible_facts['ansible_net_gather_subset'].append('ofacts')
                legacy_facts_type.remove('ofacts')

        if self.VALID_LEGACY_GATHER_SUBSETS:
            self.get_network_legacy_facts(FACT_LEGACY_SUBSETS, legacy_facts_type)

        return self.ansible_facts, self._warnings
