#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos lacp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.lacp_interfaces.lacp_interfaces import Lacp_interfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type


class Lacp_interfacesFacts(object):
    """ The nxos lacp_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lacp_interfacesArgs.argument_spec
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
        """ Populate the facts for lacp_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = connection.get('show running-config | section ^interface')

        resources = data.split('interface ')
        for resource in resources:
            if resource and re.search(r'lacp', resource):
                obj = self.render_config(self.generated_spec, resource)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('lacp_interfaces', None)
        facts = {}
        if objs:
            facts['lacp_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['lacp_interfaces'].append(utils.remove_empties(cfg))

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

        match = re.search(r'^(\S+)', conf)
        intf = match.group(1)
        if get_interface_type(intf) == 'unknown':
            return {}
        config['name'] = intf
        config['port_priority'] = utils.parse_conf_arg(conf, 'lacp port-priority')
        config['rate'] = utils.parse_conf_arg(conf, 'lacp rate')
        config['mode'] = utils.parse_conf_arg(conf, 'mode')
        suspend_individual = re.search(r'no lacp suspend-individual', conf)
        if suspend_individual:
            config['suspend_individual'] = False
        max_links = utils.parse_conf_arg(conf, 'lacp max-bundle')
        if max_links:
            config['links']['max'] = max_links
        min_links = utils.parse_conf_arg(conf, 'lacp min-links')
        if min_links:
            config['links']['min'] = min_links
        graceful = re.search(r'no lacp graceful-convergence', conf)
        if graceful:
            config['convergence']['gracefule'] = False
        vpc = re.search(r'lacp vpc-convergence', conf)
        if vpc:
            config['convergence']['vpc'] = True

        return utils.remove_empties(config)
