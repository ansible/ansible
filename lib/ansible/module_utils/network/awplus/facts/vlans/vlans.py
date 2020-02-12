#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus vlans fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from copy import deepcopy


from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.argspec.vlans.vlans import VlansArgs


class VlansFacts(object):
    """ The awplus vlans fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlansArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_vlans_facts(self, connection):
        return connection.get('show vlan all')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vlans
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:
            pass

        objs = []
        if not data:
            data = self.get_vlans_facts(connection)
        config = data.split('\n')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['vlans'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                if not isinstance(cfg, str):
                    facts['vlans'].append(utils.remove_empties(cfg))
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

        match = re.search(r'(\d+)\s+(\S+)\s+(\w+)\s+(\w+)', conf, re.M)

        if match:
            config['vlan_id'] = int(match.group(1))
            config['name'] = match.group(2)

            state = match.group(4)
            if state == 'ACTIVE':
                config['state'] = 'enable'
            elif state == 'SUSPEND':
                config['state'] = 'disable'

        return utils.remove_empties(config)
