#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr acl_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.argspec.acl_interfaces.acl_interfaces import Acl_interfacesArgs


class Acl_interfacesFacts(object):
    """ The iosxr acl_interfaces fact class
    """
    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Acl_interfacesArgs.argument_spec
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
        """ Populate the facts for acl_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = connection.get_config(flags='interface')

        interfaces = data.split('interface ')

        objs = []
        for interface in interfaces:
            obj = self.render_config(self.generated_spec, interface)
            if obj:
                objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('acl_interfaces', None)
        facts = {}
        facts['acl_interfaces'] = []
        params = utils.validate_config(self.argument_spec, {'config': objs})
        for cfg in params['config']:
            facts['acl_interfaces'].append(utils.remove_empties(cfg))

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
        config['access_groups'] = []
        map_dir = {'ingress': 'in', 'egress': 'out'}

        match = re.search(r'(?:preconfigure)*(?:\s*)(\S+)', conf, re.M)
        if match:
            config['name'] = match.group(1)
            acls = {'ipv4': [], 'ipv6': []}
            for item in conf.split('\n'):
                item = item.strip()
                if item.startswith('ipv4 access-group'):
                    acls['ipv4'].append(item)
                elif item.startswith('ipv6 access-group'):
                    acls['ipv6'].append(item)

            for key, value in iteritems(acls):
                if value:
                    entry = {'afi': key, 'acls': []}
                    for item in value:
                        entry['acls'].append({'name': item.split()[2], 'direction': map_dir[item.split()[3]]})
                    config['access_groups'].append(entry)

            config['access_groups'] = sorted(config['access_groups'], key=lambda i: i['afi'])

        return utils.remove_empties(config)
