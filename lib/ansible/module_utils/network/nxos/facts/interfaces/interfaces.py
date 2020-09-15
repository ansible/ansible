#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type
from ansible.module_utils.network.nxos.nxos import default_intf_enabled


class InterfacesFacts(object):
    """ The nxos interfaces fact class
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

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get("show running-config all | incl 'system default switchport'")
            data += "\n" + connection.get(
                "show running-config | section ^interface"
            )

        # Collect device defaults & per-intf defaults
        self.render_system_defaults(data)
        intf_defs = {'sysdefs': self.sysdefs}

        config = data.split('interface ')
        default_interfaces = []
        for conf in config:
            conf = conf.strip()
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    intf_defs[obj['name']] = obj.pop('enabled_def', None)
                    if len(obj.keys()) > 1:
                        objs.append(obj)
                    elif len(obj.keys()) == 1:
                        # Existing-but-default interfaces are not included in the
                        # objs list; however a list of default interfaces is
                        # necessary to prevent idempotence issues and to help
                        # with virtual interfaces that haven't been created yet.
                        default_interfaces.append(obj['name'])

        ansible_facts['ansible_network_resources'].pop('interfaces', None)
        facts = {}
        facts['interfaces'] = []
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['interfaces'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)
        ansible_facts['ansible_network_resources']['default_interfaces'] = default_interfaces
        ansible_facts['intf_defs'] = intf_defs
        return ansible_facts

    def _device_info(self):
        return self._module._capabilities.get('device_info', {})

    def render_system_defaults(self, config):
        """Collect user-defined-default states for 'system default switchport' configurations.
        These configurations determine default L2/L3 modes and enabled/shutdown
        states. The default values for user-defined-default configurations may
        be different for legacy platforms.
        Notes:
        - L3 enabled default state is False on N9K,N7K but True for N3K,N6K
        - Changing L2-L3 modes may change the default enabled value.
        - '(no) system default switchport shutdown' only applies to L2 interfaces.
        """
        platform = self._device_info().get('network_os_platform', '')
        L3_enabled = True if re.search('N[356]K', platform) else False
        sysdefs = {
            'mode': None,
            'L2_enabled': None,
            'L3_enabled': L3_enabled
        }
        pat = '(no )*system default switchport$'
        m = re.search(pat, config, re.MULTILINE)
        if m:
            sysdefs['mode'] = 'layer3' if 'no ' in m.groups() else 'layer2'

        pat = '(no )*system default switchport shutdown$'
        m = re.search(pat, config, re.MULTILINE)
        if m:
            sysdefs['L2_enabled'] = True if 'no ' in m.groups() else False

        self.sysdefs = sysdefs

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
        config['name'] = intf
        config['description'] = utils.parse_conf_arg(conf, 'description')
        config['speed'] = utils.parse_conf_arg(conf, 'speed')
        config['mtu'] = utils.parse_conf_arg(conf, 'mtu')
        config['duplex'] = utils.parse_conf_arg(conf, 'duplex')
        config['mode'] = utils.parse_conf_cmd_arg(conf, 'switchport', 'layer2', 'layer3')

        config['enabled'] = utils.parse_conf_cmd_arg(conf, 'shutdown', False, True)

        # Capture the default 'enabled' state, which may be interface-specific
        config['enabled_def'] = default_intf_enabled(name=intf, sysdefs=self.sysdefs, mode=config['mode'])

        config['fabric_forwarding_anycast_gateway'] = utils.parse_conf_cmd_arg(conf, 'fabric forwarding mode anycast-gateway', True)
        config['ip_forward'] = utils.parse_conf_cmd_arg(conf, 'ip forward', True)

        interfaces_cfg = utils.remove_empties(config)
        return interfaces_cfg
