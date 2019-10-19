#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for ce
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.network.cloudengine.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.common.facts.facts import FactsBase
from ansible.module_utils.network.cloudengine.facts.lldp.lldp import LldpFacts
from ansible.module_utils.network.cloudengine.facts.lldp_interface.lldp_interface import LldpInterfaceFacts


FACT_LEGACY_SUBSETS = {}
FACT_RESOURCE_SUBSETS = dict(
    default=FactsArgs,
    lldp=LldpFacts,
    lldp_interface=LldpInterfaceFacts,
)


class Facts(FactsBase):
    """ The fact class for ce
    """

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for ce

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
