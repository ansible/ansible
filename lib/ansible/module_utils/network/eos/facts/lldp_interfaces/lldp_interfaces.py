#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos lldp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.lldp_interfaces.lldp_interfaces import Lldp_interfacesArgs


class Lldp_interfacesFacts(object):
    """ The eos lldp_interfaces fact class
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
        if connection:  # just for linting purposes, remove
            pass

        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = ("resource rsrc_a\n"
                    "  a_bool true\n"
                    "  a_string choice_a\n"
                    "  resource here\n"
                    "resource rscrc_b\n"
                    "  key is property01 value is value end\n"
                    "  an_int 10\n")

        # split the config into instances of the resource
        resource_delim = 'resource'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern,
                                                   data,
                                                   re.DOTALL)]

        objs = []
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('lldp_interfaces', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['lldp_interfaces'] = params['config']

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
        config['name'] = utils.parse_conf_arg(conf, 'resource')
        config['some_string'] = utils.parse_conf_arg(conf, 'a_string')

        match = re.match(r'.*key is property01 (\S+)',
                         conf, re.MULTILINE | re.DOTALL)
        if match:
            config['some_dict']['property_01'] = match.groups()[0]

        a_bool = utils.parse_conf_arg(conf, 'a_bool')
        if a_bool == 'true':
            config['some_bool'] = True
        elif a_bool == 'false':
            config['some_bool'] = False
        else:
            config['some_bool'] = None

        try:
            config['some_int'] = int(utils.parse_conf_arg(conf, 'an_int'))
        except TypeError:
            config['some_int'] = None
        return utils.remove_empties(config)
