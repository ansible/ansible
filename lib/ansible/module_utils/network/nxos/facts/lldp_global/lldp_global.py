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
        
        objs = []
        objs = self.render_config(self.generated_spec, data)

        ansible_facts['ansible_network_resources'].pop('lldp_global', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['lldp_global'] = params['config']

        ansible_facts['ansible_network_resources'].update(utils.remove_empties(facts))
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
 
        data = re.split('\n',conf)
        if len(data)>1:
            for key in data:
                words = key.split()
                if len(words) > 0 and len(words) < 4:
                    if 'holdtime' in words[1]:
                        config['holdtime'] = words[2]
                    elif 'reinit' in words[1]:
                        config['reinit'] = words[2]
                    elif 'timer' in words[1]:
                        config['timer'] = words[2]
                    elif 'portid-subtype' in words[1]:      
                        config['port_id'] = words[2]
               
                elif len(words) > 3:    
                    if 'dcbxp' in words[3]:
                        config['tlv_select']['dcbxp'] = False
                    elif 'management-address' in words[3]:
                        if 'v4' in words[4]:
                            config['tlv_select']['management_address']['v4'] = False
                        elif 'v6' in words[4]:
                            config['tlv_select']['management_address']['v6'] = False
                    elif 'port' in words[3]:
                        if 'description' in words[3]:
                            config['tlv_select']['port']['description'] = False
                        if 'vlan' in words[3]:
                            config['tlv_select']['port']['vlan'] = False
                    elif 'power' in words[3]:
                        config['tlv_select']['power_management'] = False
                    elif 'system' in words[3]:
                        if 'name' in words[3]:
                            config['tlv_select']['system']['name'] = False
                        elif 'capabilities' in words[3]:
                            config['tlv_select']['system']['capabilities'] = False
                        elif 'description' in words[3]:
                            config['tlv_select']['system']['description'] = False

        return utils.remove_empties(config) 

