#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lacp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.utils.utils import get_interface_type, normalize_interface
from ansible.module_utils.network.ios.argspec.lacp_interfaces.lacp_interfaces import Lacp_InterfacesArgs


class Lacp_InterfacesFacts(object):
    """ The ios_lacp_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):

        self._module = module
        self.argument_spec = Lacp_InterfacesArgs.argument_spec
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
        if connection:
            pass

        objs = []
        if not data:
            data = connection.get('show running-config | section ^interface')
        # operate on a collection of resource x
        config = data.split('interface ')

        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
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

        config['name'] = normalize_interface(intf)
        port_priority = utils.parse_conf_arg(conf, 'lacp port-priority')
        max_bundle = utils.parse_conf_arg(conf, 'lacp max-bundle')
        if port_priority:
            config['port_priority'] = int(port_priority)
        if 'lacp fast-switchover' in conf:
            config['fast_switchover'] = True
        if max_bundle:
            config['max_bundle'] = int(max_bundle)

        return utils.remove_empties(config)
