#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type, normalize_interface


class Lag_interfacesFacts(object):
    """ The nxos lag_interfaces fact class
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
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get('show running-config | include channel-group')
        config = re.split('(\n  |)channel-group ', data)
        config = list(dict.fromkeys(config))
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf, connection)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('lag_interfaces', None)
        facts = {}
        if objs:
            facts['lag_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['lag_interfaces'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def get_members(self, id, connection):
        """
        Returns members associated with a channel-group

        :param name: The channel group
        :rtype: list
        :returns: Members
        """
        members = []
        data = connection.get('show port-channel summary')
        match = re.search(r'{0} (.+)(|\n)'.format(id), data)
        if match:
            interfaces = re.search(r'Eth\d(.+)$', match.group())
            if interfaces:
                for i in interfaces.group().split():
                    if get_interface_type(i[:-3]) != 'unknown':
                        members.append(normalize_interface(i[:-3]))

        return members

    def render_config(self, spec, conf, connection):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        match = re.search(r'(\d+)( |)(force )?(mode \S+)?', conf, re.M)
        if match:
            matches = match.groups()
            config['name'] = 'port-channel' + str(matches[0])
            config['members'] = []
            members = self.get_members(config['name'].strip('port-channel'), connection)
            if members:
                for m in members:
                    m_dict = {}
                    if matches[2]:
                        m_dict['force'] = matches[2]
                    if matches[3]:
                        m_dict['mode'] = matches[3][5:]
                    m_dict['member'] = m
                    config['members'].append(m_dict)
        else:
            config = {}

        lag_intf_cfg = utils.remove_empties(config)
        # if lag interfaces config is not present return empty dict
        if len(lag_intf_cfg) == 1:
            return {}
        else:
            return lag_intf_cfg
