# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import re

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs


class Lag_interfacesFacts(object):
    """ The eos lag_interfaces fact class
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
        :param data: previously collected configuration
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get('show running-config | section ^interface')

        # split the config into instances of the resource
        resource_delim = 'interface'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern,
                                                   data,
                                                   re.DOTALL)]

        objs = {}
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    group_name = obj['name']
                    if group_name in objs and "members" in obj:
                        config = objs[group_name]
                        if "members" not in config:
                            config["members"] = []
                        objs[group_name]['members'].extend(obj['members'])
                    else:
                        objs[group_name] = obj
        objs = list(objs.values())
        facts = {'lag_interfaces': []}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['lag_interfaces'] = [utils.remove_empties(cfg) for cfg in params['config']]
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
        interface_name = utils.parse_conf_arg(conf, 'interface')
        if interface_name.startswith("Port-Channel"):
            config["name"] = interface_name
            return utils.remove_empties(config)

        interface = {'member': interface_name}
        match = re.match(r'.*channel-group (\d+) mode (\S+)', conf, re.MULTILINE | re.DOTALL)
        if match:
            config['name'], interface['mode'] = match.groups()
            config["name"] = "Port-Channel" + config["name"]
            config['members'] = [interface]

        return utils.remove_empties(config)
