#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""
The awplus interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy


from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.utils.utils import get_interface_type, normalize_interface
from ansible.module_utils.network.awplus.argspec.interfaces.interfaces import InterfacesArgs


class InterfacesFacts(object):
    """ The awplus interfaces fact class
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

    def get_device_data(self, connection):
        return connection.get('show running-config interface')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            # CHECK PRIVILEGE BEFOREHAND
            data = self.get_device_data(connection)
            config = data.split('!')
            for conf in config:
                if conf:
                    obj = self.render_configs(self.generated_spec, conf)
                    if obj:
                        objs.extend(obj)

        facts = {}
        if objs:
            facts['interfaces'] = []
            params = utils.validate_config(
                self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['interfaces'].append(utils.remove_empties(cfg))
            ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_configs(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        match = re.search(r'interface (\S+)', conf)
        if match:
            intf = match.group(1)
            if get_interface_type(intf) == 'unknown':
                return {}
        else:
            return {}
        # populate facts from configuration
        port_range = re.search(r'port(\d+).(\d+).(\d+)-(\d+).(\d+).(\d+)', intf)
        if port_range:
            start = int(port_range.group(3))
            end = int(port_range.group(6))
            # Looping to produce a list of interface configuration
            intf_configs = []
            for i in range(start, end + 1):
                interface = 'port1.0.' + str(i)
                intf_configs.append(self.render_config(spec, conf, interface))
            return intf_configs
        else:
            return [self.render_config(spec, conf, intf)]

    def render_config(self, spec, conf, intf):
        config = deepcopy(spec)
        config['name'] = normalize_interface(intf)
        config['description'] = utils.parse_conf_arg(conf, 'description')
        if utils.parse_conf_arg(conf, 'speed'):
            config['speed'] = int(utils.parse_conf_arg(conf, 'speed'))
        if utils.parse_conf_arg(conf, 'mtu'):
            config['mtu'] = int(utils.parse_conf_arg(conf, 'mtu'))
        config['duplex'] = utils.parse_conf_arg(conf, 'duplex')
        enabled = utils.parse_conf_cmd_arg(conf, 'shutdown', False)
        config['enabled'] = enabled if enabled is not None else True
        return utils.remove_empties(config)
