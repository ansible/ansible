#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from copy import deepcopy
import re
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.utils.utils import get_interface_type, normalize_interface
from ansible.module_utils.network.iosxr.argspec.l2_interfaces.l2_interfaces import L2_InterfacesArgs


class L2_InterfacesFacts(object):
    """ The iosxr l2_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L2_InterfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, module, connection, data=None):
        """ Populate the facts for l2_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config interface')

        # operate on a collection of resource x
        config = data.split('interface ')
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

        self.ansible_facts['ansible_network_resources'].update(facts)
        return self.ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        match = re.search(r'^(\S+)', conf)

        if len(match.group().split('.')) > 1:
            sub_match = re.search(r'^(\S+ \S+)', conf)
            if sub_match:
                intf = sub_match.group()
                config['name'] = intf
            else:
                intf = match.group(1)
                config['name'] = intf
        else:
            intf = match.group(1)
            if get_interface_type(intf) == 'unknown':
                return {}
            # populate the facts from the configuration
            config['name'] = normalize_interface(intf)
        native_vlan = re.search(r"dot1q native vlan (\d+)", conf)
        if native_vlan:
            config["native_vlan"] = {"vlan": int(native_vlan.group(1))}
        if 'l2transport' in config['name']:
            config['q_vlan'] = utils.parse_conf_arg(conf, 'dot1q vlan')
        else:
            config['q_vlan'] = utils.parse_conf_arg(conf, 'encapsulation dot1q')

        if utils.parse_conf_arg(conf, 'propagate'):
            config['propagate'] = True
        config['l2protocol_cdp'] = utils.parse_conf_arg(conf, 'l2protocol cdp')
        config['l2protocol_pvst'] = utils.parse_conf_arg(conf, 'l2protocol pvst')
        config['l2protocol_stp'] = utils.parse_conf_arg(conf, 'l2protocol stp')
        config['l2protocol_vtp'] = utils.parse_conf_arg(conf, 'l2protocol vtp')
        if config.get('propagate') or config.get('l2protocol_cdp') or config.get('l2protocol_pvst') or \
                config.get('l2protocol_stp') or config.get('l2protocol_vtp'):
            config['l2transport'] = True

        return utils.remove_empties(config)
