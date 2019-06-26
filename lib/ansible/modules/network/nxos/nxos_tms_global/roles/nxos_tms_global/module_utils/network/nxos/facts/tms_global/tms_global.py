#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos tms_global fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy
from ansible.module_utils.network.nxos.facts.base import FactsBase
from ansible.module_utils.network.nxos.cmdref.tms_global import TMS_CMD_REF
from ansible.module_utils.network.nxos.nxos import NxosCmdRef, normalize_interface


class Tms_globalFacts(FactsBase):
    """ The nxos tms_global fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for tms_global
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if module:  # just for linting purposes, remove
            pass
        if connection:  # just for linting purposes, remove
            pass

        cmd_ref = NxosCmdRef(module, TMS_CMD_REF)
        cmd_ref.set_context()
        cmd_ref.get_existing()

        objs = []
        objs = self.render_config(self.generated_spec, cmd_ref)
        facts = {}
        if objs:
            facts['tms_global'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, cmd_ref):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param cmd_ref: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        for key in config.keys():
            if cmd_ref._ref[key].get('existing'):
                if isinstance(config[key], dict):
                    for k in config[key].keys():
                        config[key][k] = cmd_ref._ref[key]['existing'][0][k]
                    continue
                config[key] = cmd_ref._ref[key]['existing'][0]

        return self.generate_final_config(config)
