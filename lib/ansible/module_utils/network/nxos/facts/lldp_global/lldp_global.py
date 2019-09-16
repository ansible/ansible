#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos lldp_global fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.lldp_global.lldp_global import Lldp_globalArgs


class Lldp_globalFacts(object):
    """ The nxos lldp_global fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lldp_globalArgs.argument_spec
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
        """ Populate the facts for lldp_global
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = connection.get('show running-config | include lldp')

        objs = {}
        objs = self.render_config(self.generated_spec, data)
        ansible_facts['ansible_network_resources'].pop('lldp_global', None)
        facts = {}
        if objs:
            params = utils.validate_config(
                self.argument_spec, {'config': objs})
            facts['lldp_global'] = params['config']
            facts = utils.remove_empties(facts)
        ansible_facts['ansible_network_resources'].update((facts))
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
        conf = re.split('\n', conf)
        for command in conf:
            param = re.search(
                r'(.*)lldp (\w+(-?)\w+)',
                command)  # get the word after 'lldp'
            if param:
                # get the nested-dict/value for that param
                key2 = re.search(r'%s(.*)' % param.group(2), command)
                key2 = key2.group(1).strip()
                key1 = param.group(2).replace('-', '_')

                if key1 == 'portid_subtype':
                    key1 = 'port_id'
                    config[key1] = key2
                elif key1 == 'tlv_select':
                    key2 = key2.split()
                    key2[0] = key2[0].replace('-', '_')
                    if len(key2) == 1:
                        if 'port' in key2[0] or 'system' in key2[0]:  # nested dicts
                            key2 = key2[0].split('_')
                            # config[tlv_select][system][name]=False
                            config[key1][key2[0]][key2[1]] = False
                        else:
                            # config[tlv_select][dcbxp]=False
                            config[key1][key2[0]] = False
                    else:
                        # config[tlv_select][management_address][v6]=False
                        config[key1][key2[0]][key2[1]] = False
                else:
                    config[key1] = key2  # config[reinit]=4
        return utils.remove_empties(config)
