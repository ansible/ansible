# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import re

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.interfaces.interfaces import InterfacesArgs


class InterfacesFacts(object):
    """ The eos interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = InterfacesArgs.argument_spec
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
        """ Populate the facts for interfaces

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected configuration
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
        facts = {'interfaces': []}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['interfaces'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

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
        config['name'] = re.match(r'(\S+)', conf).group(1)
        description = utils.parse_conf_arg(conf, 'description')
        if description is not None:
            config['description'] = description.replace('"', '')
        shutdown = utils.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['enabled'] = shutdown if shutdown is False else True
        config['mtu'] = utils.parse_conf_arg(conf, 'mtu')

        speed_pair = utils.parse_conf_arg(conf, 'speed')
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

        return utils.remove_empties(config)
