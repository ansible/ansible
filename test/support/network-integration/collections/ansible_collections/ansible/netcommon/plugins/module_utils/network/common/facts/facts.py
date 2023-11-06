#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts base class
this contains methods common to all facts subsets
"""
from __future__ import annotations

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.network import (
    get_resource_connection,
)
from ansible.module_utils.six import iteritems


class FactsBase(object):
    """
    The facts base class
    """

    def __init__(self, module):
        self._module = module
        self._warnings = []
        self._gather_subset = module.params.get("gather_subset")
        self._gather_network_resources = module.params.get(
            "gather_network_resources"
        )
        self._connection = None
        if module.params.get("state") not in ["rendered", "parsed"]:
            self._connection = get_resource_connection(module)

        self.ansible_facts = {"ansible_network_resources": {}}
        self.ansible_facts["ansible_net_gather_network_resources"] = list()
        self.ansible_facts["ansible_net_gather_subset"] = list()

        if not self._gather_subset:
            self._gather_subset = ["!config"]
        if not self._gather_network_resources:
            self._gather_network_resources = ["!all"]

    def gen_runable(self, subsets, valid_subsets, resource_facts=False):
        """ Generate the runable subset

        :param module: The module instance
        :param subsets: The provided subsets
        :param valid_subsets: The valid subsets
        :param resource_facts: A boolean flag
        :rtype: list
        :returns: The runable subsets
        """
        runable_subsets = set()
        exclude_subsets = set()
        minimal_gather_subset = set()
        if not resource_facts:
            minimal_gather_subset = frozenset(["default"])

        for subset in subsets:
            if subset == "all":
                runable_subsets.update(valid_subsets)
                continue
            if subset == "min" and minimal_gather_subset:
                runable_subsets.update(minimal_gather_subset)
                continue
            if subset.startswith("!"):
                subset = subset[1:]
                if subset == "min":
                    exclude_subsets.update(minimal_gather_subset)
                    continue
                if subset == "all":
                    exclude_subsets.update(
                        valid_subsets - minimal_gather_subset
                    )
                    continue
                exclude = True
            else:
                exclude = False

            if subset not in valid_subsets:
                self._module.fail_json(
                    msg="Subset must be one of [%s], got %s"
                    % (
                        ", ".join(sorted(list(valid_subsets))),
                        subset,
                    )
                )

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(valid_subsets)
        runable_subsets.difference_update(exclude_subsets)
        return runable_subsets

    def get_network_resources_facts(
        self, facts_resource_obj_map, resource_facts_type=None, data=None
    ):
        """
        :param fact_resource_subsets:
        :param data: previously collected configuration
        :return:
        """
        if not resource_facts_type:
            resource_facts_type = self._gather_network_resources

        restorun_subsets = self.gen_runable(
            resource_facts_type,
            frozenset(facts_resource_obj_map.keys()),
            resource_facts=True,
        )
        if restorun_subsets:
            self.ansible_facts["ansible_net_gather_network_resources"] = list(
                restorun_subsets
            )
            instances = list()
            for key in restorun_subsets:
                fact_cls_obj = facts_resource_obj_map.get(key)
                if fact_cls_obj:
                    instances.append(fact_cls_obj(self._module))
                else:
                    self._warnings.extend(
                        [
                            "network resource fact gathering for '%s' is not supported"
                            % key
                        ]
                    )

            for inst in instances:
                inst.populate_facts(self._connection, self.ansible_facts, data)

    def get_network_legacy_facts(
        self, fact_legacy_obj_map, legacy_facts_type=None
    ):
        if not legacy_facts_type:
            legacy_facts_type = self._gather_subset

        runable_subsets = self.gen_runable(
            legacy_facts_type, frozenset(fact_legacy_obj_map.keys())
        )
        if runable_subsets:
            facts = dict()
            # default subset should always returned be with legacy facts subsets
            if "default" not in runable_subsets:
                runable_subsets.add("default")
            self.ansible_facts["ansible_net_gather_subset"] = list(
                runable_subsets
            )

            instances = list()
            for key in runable_subsets:
                instances.append(fact_legacy_obj_map[key](self._module))

            for inst in instances:
                inst.populate()
                facts.update(inst.facts)
                self._warnings.extend(inst.warnings)

            for key, value in iteritems(facts):
                key = "ansible_net_%s" % key
                self.ansible_facts[key] = value
