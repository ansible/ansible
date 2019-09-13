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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import re

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs


class L3_interfacesFacts(object):
    """ The eos l3_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L3_interfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for l3_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected configuration
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
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['l3_interfaces'] = [utils.remove_empties(cfg) for cfg in params['config']]
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

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

        config['name'] = utils.parse_conf_arg(conf, 'interface')

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

        return utils.remove_empties(config)
