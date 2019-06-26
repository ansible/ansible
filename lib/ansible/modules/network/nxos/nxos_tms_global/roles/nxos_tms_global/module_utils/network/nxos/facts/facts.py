#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for nxos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible.module_utils.six import iteritems
from ansible.module_utils.network. \
    nxos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network. \
    nxos.argspec.tms_global.tms_global import Tms_globalArgs
from ansible.module_utils.network. \
    nxos.facts.base import FactsBase
from ansible.module_utils.network. \
    nxos.facts.tms_global.tms_global import Tms_globalFacts


FACT_SUBSETS = {}


class Facts(FactsArgs, FactsBase):  # pylint: disable=R0903
    """ The fact class for nxos
    """

    VALID_GATHER_SUBSETS = frozenset(FACT_SUBSETS.keys())

    @staticmethod
    def gen_runable(module, subsets, valid_subsets):
        """ Generate the runable subset

        :param module: The module instance
        :param subsets: The provided subsets
        :param valid_subsets: The valid subsets
        :rtype: list
        :returns: The runable subsets
        """
        runable_subsets = set()
        exclude_subsets = set()
        minimal_gather_subset = frozenset(['default'])

        for subset in subsets:
            if subset == 'all':
                runable_subsets.update(valid_subsets)
                continue
            if subset == 'min' and minimal_gather_subset:
                runable_subsets.update(minimal_gather_subset)
                continue
            if subset.startswith('!'):
                subset = subset[1:]
                if subset == 'min':
                    exclude_subsets.update(minimal_gather_subset)
                    continue
                if subset == 'all':
                    exclude_subsets.update(
                        valid_subsets - minimal_gather_subset)
                    continue
                exclude = True
            else:
                exclude = False

            if subset not in valid_subsets:
                module.fail_json(msg='Bad subset')

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(valid_subsets)
        runable_subsets.difference_update(exclude_subsets)

        return runable_subsets

    def get_facts(self, module, connection, gather_subset=None,
                  gather_network_resources=None):
        """ Collect the facts for nxos

        :param module: The module instance
        :param connection: The device connection
        :param gather_subset: The facts subset to collect
        :param gather_network_resources: The resource subset to collect
        :rtype: dict
        :returns: the facts gathered
        """
        if not gather_subset:
            gather_subset = ['!config']
        if not gather_network_resources:
            gather_network_resources = ['all']
        warnings = []
        self.ansible_facts['gather_network_resources'] = list()
        self.ansible_facts['gather_subset'] = list()

        valnetres = self.argument_spec['gather_network_resources'].\
            get('choices', [])
        if valnetres:
            if 'all' in valnetres:
                valnetres.remove('all')

        if valnetres:
            restorun = self.gen_runable(module, gather_network_resources,
                                        valnetres)
            if restorun:
                self.ansible_facts['gather_network_resources'] = list(restorun)
                for attr in restorun:
                    getattr(self, '_get_%s' % attr, {})(module, connection)

        if self.VALID_GATHER_SUBSETS:
            runable_subsets = self.gen_runable(module,
                                               gather_subset,
                                               self.VALID_GATHER_SUBSETS)

            if runable_subsets:
                facts = dict()
                self.ansible_facts['gather_subset'] = list(runable_subsets)

                instances = list()
                for key in runable_subsets:
                    instances.append(FACT_SUBSETS[key](module))

                for inst in instances:
                    inst.populate()
                    facts.update(inst.facts)
                    warnings.extend(inst.warnings)

                for key, value in iteritems(facts):
                    key = 'ansible_net_%s' % key
                    self.ansible_facts[key] = value

        return self.ansible_facts, warnings

    @staticmethod
    def _get_tms_global(module, connection):
        return Tms_globalFacts(
            Tms_globalArgs.argument_spec,
            'config', 'options').populate_facts(module, connection)
