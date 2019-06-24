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
from ansible.module_utils.network. \
    nxos.facts.base import FactsBase


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

        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = ("resource rsrc_a\n"
                    "  a_bool true\n"
                    "  a_string choice_a\n"
                    "  resource here\n"
                    "resource rscrc_b\n"
                    "  key is property01 value is value end\n"
                    "  an_int 10\n")

        # split the config into instances of the resource
        resource_delim = 'resource'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern,
                                                   data,
                                                   re.DOTALL)]

        objs = []
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['tms_global'] = objs
        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        config['name'] = self.parse_conf_arg(conf, 'resource')
        config['some_string'] = self.parse_conf_arg(conf, 'a_string')

        match = re.match(r'.*key is property01 (\S+)',
                         conf, re.MULTILINE | re.DOTALL)
        if match:
            config['some_dict']['property_01'] = match.groups()[0]

        a_bool = self.parse_conf_arg(conf, 'a_bool')
        if a_bool == 'true':
            config['some_bool'] = True
        elif a_bool == 'false':
            config['some_bool'] = False
        else:
            config['some_bool'] = None

        try:
            config['some_int'] = int(self.parse_conf_arg(conf, 'an_int'))
        except TypeError:
            config['some_int'] = None

        return self.generate_final_config(config)
