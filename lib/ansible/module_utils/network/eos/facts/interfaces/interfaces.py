#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from copy import deepcopy
import re

from ansible.module_utils.network.eos.facts.base import FactsBase


class InterfacesFacts(FactsBase):
    """ The eos interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for interfaces

        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get('show running-config | section ^interface')

        # operate on a collection of resource x
        config = data.split('interface ')
        objs = []
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['interfaces'] = objs
        self.ansible_facts['net_configuration'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        # populate the facts from the configuration
        config['name'] = re.match(r'(\S+)', conf).group(1).replace('"', '')
        description = self.parse_conf_arg(conf, 'description')
        if description is not None:
            config['description'] = description.replace('"', '')
        shutdown = self.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['enable'] = shutdown if shutdown is False else True
        config['mtu'] = self.parse_conf_arg(conf, 'mtu')

        speed_pair = self.parse_conf_arg(conf, 'speed')
        if speed_pair:
            state = speed_pair.split()
            if state[0] == 'forced':
                state = state[1]
            else:
                state = state[0]

            if state == 'auto':
                config['duplex'] = state
            else:
                # remaining options are all e.g., 10half or 40gfull
                config['speed'] = state[:-4]
                config['duplex'] = state[-4:]

        return self.generate_final_config(config)
