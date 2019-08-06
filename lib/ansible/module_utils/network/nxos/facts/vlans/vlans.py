#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos vlans fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.common.utils import parse_conf_arg, parse_conf_cmd_arg
from ansible.module_utils.network.nxos.argspec.vlans.vlans import VlansArgs


class VlansFacts(object):
    """ The nxos vlans fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlansArgs.argument_spec
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
        """ Populate the facts for vlans
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config | section ^vlan')
        vlans = re.split(r'(,|-)', data.split()[1])
        for v in vlans:
            if not v.isdigit():
                vlans.remove(v)

        config = re.split(r'(^|\n)vlan', data)
        for conf in config:
            conf = conf.strip()
            if conf:
                if conf[0] in vlans:
                    vlans.remove(conf[0])
                    obj = self.render_config(self.generated_spec, conf)
                    if obj and len(obj.keys()) > 1:
                        objs.append(obj)

        for v in vlans:
            obj = self.render_config(self.generated_spec, v)
            if obj:
                objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('vlans', None)
        facts = {}
        if objs:
            facts['vlans'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['vlans'].append(utils.remove_empties(cfg))

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
        if len(conf) == 1:
            return utils.remove_empties({'vlan_id': conf})

        match = re.search(r'^(\S+)?', conf, re.M)
        if match:
            if len(match.group(1)) == 1:
                config['vlan_id'] = match.group(1)
                config['name'] = parse_conf_arg(conf, 'name')
                config['mode'] = parse_conf_arg(conf, 'mode')
                config['mapped_vni'] = parse_conf_arg(conf, 'vn-segment')
                config['state'] = parse_conf_arg(conf, 'state')
                admin_state = parse_conf_cmd_arg(conf, 'shutdown', 'down', 'up')
                if admin_state == 'up':
                    config['enabled'] = True
                elif admin_state == 'down':
                    config['enabled'] = False

        vlans_cfg = utils.remove_empties(config)
        return vlans_cfg
