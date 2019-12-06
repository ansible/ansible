#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for ios
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.ios.facts.interfaces.interfaces import InterfacesFacts
from ansible.module_utils.network.ios.facts.l2_interfaces.l2_interfaces import L2_InterfacesFacts
from ansible.module_utils.network.ios.facts.vlans.vlans import VlansFacts
from ansible.module_utils.network.ios.facts.lag_interfaces.lag_interfaces import Lag_interfacesFacts
from ansible.module_utils.network.ios.facts.lacp.lacp import LacpFacts
from ansible.module_utils.network.ios.facts.lacp_interfaces.lacp_interfaces import Lacp_InterfacesFacts
from ansible.module_utils.network.ios.facts.lldp_global.lldp_global import Lldp_globalFacts
from ansible.module_utils.network.ios.facts.lldp_interfaces.lldp_interfaces import Lldp_InterfacesFacts
from ansible.module_utils.network.ios.facts.l3_interfaces.l3_interfaces import L3_InterfacesFacts
from ansible.module_utils.network.ios.facts.legacy.base import Default, Hardware, Interfaces, Config


FACT_LEGACY_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config
)

FACT_RESOURCE_SUBSETS = dict(
    interfaces=InterfacesFacts,
    l2_interfaces=L2_InterfacesFacts,
    vlans=VlansFacts,
    lag_interfaces=Lag_interfacesFacts,
    lacp=LacpFacts,
    lacp_interfaces=Lacp_InterfacesFacts,
    lldp_global=Lldp_globalFacts,
    lldp_interfaces=Lldp_InterfacesFacts,
    l3_interfaces=L3_InterfacesFacts,
)


class Facts(FactsBase):
    """ The fact class for ios
    """

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for ios
        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(FACT_RESOURCE_SUBSETS, resource_facts_type, data)

        if self.VALID_LEGACY_GATHER_SUBSETS:
            self.get_network_legacy_facts(FACT_LEGACY_SUBSETS, legacy_facts_type)

        return self.ansible_facts, self._warnings
