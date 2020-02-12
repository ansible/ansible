#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus static_lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.argspec.static_lag_interfaces.static_lag_interfaces import Static_Lag_interfacesArgs
from ansible.module_utils.network.awplus.utils.utils import get_interface_type, normalize_interface


class Static_Lag_interfacesFacts(object):
    """ The awplus static_lag_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Static_Lag_interfacesArgs.argument_spec
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
        """ Populate the facts for lag_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = self.get_device_data(connection)
        # operate on a collection of resource x
        config = data.split('!')
        for conf in config:
            if conf:
                objects = self.render_configs(self.generated_spec, conf)
                for obj in objects:
                    if obj:
                        if not obj.get('members'):
                            obj.update({'members': []})
                        objs.append(obj)

        # for appending members configured with same channel-group
        for each in range(len(objs)):
            if each < (len(objs) - 1):
                if objs[each]['name'] == objs[each + 1]['name']:
                    objs[each]['members'].append(objs[each + 1]['members'][0])
                    del objs[each + 1]
        facts = {}

        if objs:
            facts['lag_interfaces'] = []
            params = utils.validate_config(
                self.argument_spec, {'config': objs})

            for cfg in params['config']:
                facts['lag_interfaces'].append(utils.remove_empties(cfg))
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
        port_range = re.search(
            r'port(\d+).(\d+).(\d+)-(\d+).(\d+).(\d+)', intf)
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

    def render_config(self, spec, conf, interface):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        if interface:
            intf = interface
            if intf.startswith('port'):
                config['name'] = intf
                config['members'] = []
                member_config = {}
                channel_group = re.search(r'static-channel-group (\d+)', conf)
                if channel_group:
                    channel_group_id = channel_group.group(1)
                    config['name'] = str(channel_group_id)
                    member_filters = re.search(
                        r'static-channel-group (\d+) (member-filters)', conf)
                    if member_filters and member_filters.group(2):
                        member_filters = True
                        member_config.update(
                            {'member_filters': member_filters})
                    member_config['member'] = normalize_interface(intf)
                    config['members'].append(member_config)

        return utils.remove_empties(config)
