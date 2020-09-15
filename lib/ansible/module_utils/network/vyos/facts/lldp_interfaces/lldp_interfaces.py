#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos lldp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from re import findall, search, M
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.vyos.argspec.lldp_interfaces. \
    lldp_interfaces import Lldp_interfacesArgs


class Lldp_interfacesFacts(object):
    """ The vyos lldp_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lldp_interfacesArgs.argument_spec
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
        """ Populate the facts for lldp_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get_config()

        objs = []
        lldp_names = findall(r'^set service lldp interface (\S+)', data, M)
        if lldp_names:
            for lldp in set(lldp_names):
                lldp_regex = r' %s .+$' % lldp
                cfg = findall(lldp_regex, data, M)
                obj = self.render_config(cfg)
                obj['name'] = lldp.strip("'")
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['lldp_interfaces'] = objs
            ansible_facts['ansible_network_resources'].update(facts)

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = {}
        location = {}

        civic_conf = '\n'.join(filter(lambda x: ('civic-based' in x), conf))
        elin_conf = '\n'.join(filter(lambda x: ('elin' in x), conf))
        coordinate_conf = '\n'.join(filter(lambda x: ('coordinate-based' in x), conf))
        disable = '\n'.join(filter(lambda x: ('disable' in x), conf))

        coordinate_based_conf = self.parse_attribs(
            ['altitude', 'datum', 'longitude', 'latitude'], coordinate_conf
        )
        elin_based_conf = self.parse_lldp_elin_based(elin_conf)
        civic_based_conf = self.parse_lldp_civic_based(civic_conf)
        if disable:
            config['enable'] = False
        if coordinate_conf:
            location['coordinate_based'] = coordinate_based_conf
            config['location'] = location
        elif civic_based_conf:
            location['civic_based'] = civic_based_conf
            config['location'] = location
        elif elin_conf:
            location['elin'] = elin_based_conf
            config['location'] = location

        return utils.remove_empties(config)

    def parse_attribs(self, attribs, conf):
        config = {}
        for item in attribs:
            value = utils.parse_conf_arg(conf, item)
            if value:
                value = value.strip("'")
                if item == 'altitude':
                    value = int(value)
                config[item] = value
            else:
                config[item] = None
        return utils.remove_empties(config)

    def parse_lldp_civic_based(self, conf):
        civic_based = None
        if conf:
            civic_info_list = []
            civic_add_list = findall(r"^.*civic-based ca-type (.+)", conf, M)
            if civic_add_list:
                for civic_add in civic_add_list:
                    ca = civic_add.split(' ')
                    c_add = {}
                    c_add['ca_type'] = int(ca[0].strip("'"))
                    c_add['ca_value'] = ca[2].strip("'")
                    civic_info_list.append(c_add)

                country_code = search(r'^.*civic-based country-code (.+)', conf, M)
                civic_based = {}
                civic_based['ca_info'] = civic_info_list
                civic_based['country_code'] = country_code.group(1).strip("'")
        return civic_based

    def parse_lldp_elin_based(self, conf):
        elin_based = None
        if conf:
            e_num = search(r'^.* elin (.+)', conf, M)
            elin_based = e_num.group(1).strip("'")

        return elin_based
