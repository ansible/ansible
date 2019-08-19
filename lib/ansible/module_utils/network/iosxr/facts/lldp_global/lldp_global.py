#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr lldp fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.argspec.lldp_global.lldp_global import Lldp_globalArgs


class Lldp_globalFacts(object):
    """ The iosxr lldp fact class
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
        """ Populate the facts for lldp
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get_config(flags='lldp')

        obj = {}
        if data:
            lldp_obj = self.render_config(self.generated_spec, data)
            if lldp_obj:
                obj = lldp_obj

        ansible_facts['ansible_network_resources'].pop('lldp_global', None)
        facts = {}

        params = utils.validate_config(self.argument_spec, {'config': obj})
        facts['lldp_global'] = utils.remove_empties(params['config'])

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

        for key in spec.keys():
            if key == 'subinterfaces':
                config[key] = True if 'subinterfaces enable' in conf else None

            elif key == 'tlv_select':
                for item in ['system_name', 'port_description', 'management_address', 'system_description', 'system_capabilities']:
                    config[key][item] = False if ('{0} disable'.format(item.replace('_', '-'))) in conf else None

            else:
                value = utils.parse_conf_arg(conf, key)
                config[key] = int(value) if value else value

        return config
