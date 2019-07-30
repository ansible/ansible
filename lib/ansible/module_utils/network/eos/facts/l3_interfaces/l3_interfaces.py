#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy
from ansible.module_utils.network.eos.facts.base import FactsBase


class L3_interfacesFacts(FactsBase):
    """ The eos l3_interfaces fact class
    """

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l3_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = connection.get('show running-config | section ^interface')

        # split the config into instances of the resource
        resource_delim = 'interface'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim, resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern, data, re.DOTALL)]

        objs = []
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['l3_interfaces'] = objs
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

        config['name'] = self.parse_conf_arg(conf, 'interface')

        matches = re.findall(r'.*ip address (.+)$', conf, re.MULTILINE)
        if matches:
            config["ipv4"] = []
            for match in matches:
                address, dummy, remainder = match.partition(" ")
                ipv4 = {"address": address}
                if remainder == "secondary":
                    ipv4["secondary"] = True
                config['ipv4'].append(ipv4)

        matches = re.findall(r'.*ipv6 address (.+)$', conf, re.MULTILINE)
        if matches:
            config["ipv6"] = []
            for match in matches:
                address, dummy, remainder = match.partition(" ")
                ipv6 = {"address": address}
                config['ipv6'].append(ipv6)

        return self.generate_final_config(config)
