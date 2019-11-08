#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs


class Lag_interfacesFacts(object):
    """ The iosxr lag_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lag_interfacesArgs.argument_spec
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
        """ Populate the facts for lag_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = connection.get_config(flags='interface')
            interfaces = data.split('interface ')

        objs = []

        for interface in interfaces:
            if interface.startswith("Bundle-Ether"):
                obj = self.render_config(self.generated_spec, interface, interfaces)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('lag_interfaces', None)
        facts = {}

        facts['lag_interfaces'] = []
        params = utils.validate_config(self.argument_spec, {'config': objs})
        for cfg in params['config']:
            facts['lag_interfaces'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf, data):
        """
        Render config as dictionary structure and delete keys
        from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        match = re.search(r'(Bundle-Ether)(\d+)', conf, re.M)
        if match:
            config['name'] = match.group(1) + match.group(2)
            config['load_balancing_hash'] = utils.parse_conf_arg(
                conf, 'bundle load-balancing hash')
            config['mode'] = utils.parse_conf_arg(conf, 'lacp mode')
            config['links']['max_active'] = utils.parse_conf_arg(
                conf, 'bundle maximum-active links')
            config['links']['min_active'] = utils.parse_conf_arg(
                conf, 'bundle minimum-active links')
            config['members'] = self.parse_members(match.group(2), data)

        return utils.remove_empties(config)

    def parse_members(self, bundle_id, interfaces):
        """
        Renders a list of member interfaces for every bundle
        present in running-config.

        :param bundle_id: The Bundle-Ether ID fetched from running-config
        :param interfaces: Data of all interfaces present in running-config
        :rtype: list
        :returns: A list of member interfaces
        """
        def _parse_interface(name):
            if name.startswith('preconfigure'):
                return name.split()[1]
            else:
                return name.split()[0]

        members = []
        for interface in interfaces:
            if not interface.startswith('Bu'):
                match = re.search(r'bundle id (\d+) mode (\S+)', interface, re.M)
                if match:
                    if bundle_id == match.group(1):
                        members.append(
                            {
                                'member': _parse_interface(interface),
                                'mode': match.group(2)
                            }
                        )

        return members
