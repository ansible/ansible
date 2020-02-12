#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.network.awplus.utils.utils import get_interface_type, normalize_interface


class L2_interfacesFacts(object):
    """ The awplus l2_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L2_interfacesArgs.argument_spec
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
        """ Populate the facts for l2_interfaces
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
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts['l2_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['l2_interfaces'].append(utils.remove_empties(cfg))
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
        match = re.search(r'interface (\S+)', conf)
        intf = match.group(1)

        if get_interface_type(intf) == 'unknown':
            return {}

        if intf.upper()[:2] in ('HU', 'FO', 'TW', 'TE', 'GI', 'FA', 'ET', 'PO'):
            # populate the facts from the configuration
            config['name'] = normalize_interface(intf)

            mode = utils.parse_conf_arg(conf, 'switchport mode')
            if mode == 'access':
                has_access = utils.parse_conf_arg(conf, 'switchport access vlan')
                if has_access:
                    config["access"] = {"vlan": int(has_access)}
                else:
                    config["access"] = {"vlan": 1}

            trunk = dict()
            native_vlan = utils.parse_conf_arg(conf, 'native vlan')
            if native_vlan and native_vlan != 'none':
                trunk["native_vlan"] = int(native_vlan)
            allowed_vlan = utils.parse_conf_arg(conf, 'allowed vlan')
            if allowed_vlan:
                trunk["allowed_vlans"] = allowed_vlan.split(',')
            config['trunk'] = trunk

        return utils.remove_empties(config)
