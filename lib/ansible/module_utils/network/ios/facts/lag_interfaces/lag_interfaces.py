#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios lag_interfaces fact class
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
from ansible.module_utils.network.ios.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs


class Lag_interfacesFacts(object):
    """ The ios_lag_interfaces fact class
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
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = connection.get('show running-config | section ^interface')
        # operate on a collection of resource x
        config = data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
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
            params = utils.validate_config(self.argument_spec, {'config': objs})

            for cfg in params['config']:
                facts['lag_interfaces'].append(utils.remove_empties(cfg))
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
        member_config = {}
        channel_group = utils.parse_conf_arg(conf, 'channel-group')
        if intf.startswith('Gi'):
            config['name'] = intf
            config['members'] = []
            if channel_group:
                channel_group = channel_group.split(' ')
                id = channel_group[0]
                config['name'] = 'Port-channel{0}'.format(str(id))
                if 'mode' in channel_group:
                    mode = channel_group[2]
                    member_config.update({'mode': mode})
                if 'link' in channel_group:
                    link = channel_group[2]
                    member_config.update({'link': link})
            if member_config.get('mode') or member_config.get('link'):
                member_config['member'] = normalize_interface(intf)
                config['members'].append(member_config)

        return utils.remove_empties(config)
