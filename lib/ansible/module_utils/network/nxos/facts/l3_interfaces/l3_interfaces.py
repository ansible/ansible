#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type


class L3_interfacesFacts(object):
    """ The nxos l3_interfaces fact class
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
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config | section ^interface')

        config = data.split('interface ')
        for conf in config:
            conf = conf.strip()
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('l3_interfaces', None)
        facts = {}
        if objs:
            facts['l3_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['l3_interfaces'].append(utils.remove_empties(cfg))

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
        ipv4_match = re.compile(r'\n  ip address (.*)')
        matches = ipv4_match.findall(conf)
        if matches:
            if matches[0]:
                config['ipv4'] = []
                for m in matches:
                    ipv4_conf = m.split()
                    addr = ipv4_conf[0]
                    if addr:
                        config_dict = {'address': addr}
                        if len(ipv4_conf) > 1:
                            d = ipv4_conf[1]
                            if d == 'secondary':
                                config_dict.update({'secondary': True})
                                if len(ipv4_conf) == 4:
                                    if ipv4_conf[2] == 'tag':
                                        config_dict.update({'tag': int(ipv4_conf[-1])})
                            elif d == 'tag':
                                config_dict.update({'tag': int(ipv4_conf[-1])})
                        config['ipv4'].append(config_dict)

        ipv6_match = re.compile(r'\n  ipv6 address (.*)')
        matches = ipv6_match.findall(conf)
        if matches:
            if matches[0]:
                config['ipv6'] = []
                for m in matches:
                    ipv6_conf = m.split()
                    addr = ipv6_conf[0]
                    if addr:
                        config_dict = {'address': addr}
                        if len(ipv6_conf) > 1:
                            d = ipv6_conf[1]
                            if d == 'tag':
                                config_dict.update({'tag': int(ipv6_conf[-1])})
                        config['ipv6'].append(config_dict)

        return utils.remove_empties(config)
