#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_acl_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.utils.utils import get_interface_type
from ansible.module_utils.network.ios.argspec.acl_interfaces.acl_interfaces import Acl_InterfacesArgs


class Acl_InterfacesFacts(object):
    """ The ios_acl_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Acl_InterfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_acl_interfaces_data(self, connection):
        return connection.get('sh running-config | include interface|ip access-group|ipv6 traffic-filter')

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
            data = self.get_acl_interfaces_data(connection)
        # operate on a collection of resource x
        config = data.split('interface ')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
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
        match = re.search(r'^(\S+)', conf)
        intf = match.group(1)

        if get_interface_type(intf) == 'unknown':
            return {}
        config['name'] = intf
        config['access_groups'] = []
        acl_v4_config = {}
        acl_v6_config = {}

        def common_iter_code(cmd, conf):
            # Common code for IPV4 and IPV6 config parsing
            acls = []
            re_cmd = cmd + ' (\\S+.*)'
            ip_all = re.findall(re_cmd, conf)
            for each in ip_all:
                acl = {}
                access_grp_config = each.split(' ')
                acl['name'] = access_grp_config[0]
                acl['direction'] = access_grp_config[1]
                acls.append(acl)
            return acls

        if 'ip' in conf:
            acls = common_iter_code('ip access-group', conf)
            acl_v4_config['afi'] = 'ipv4'
            acl_v4_config['acls'] = acls
            config['access_groups'].append(acl_v4_config)
        if 'ipv6' in conf:
            acls = common_iter_code('ipv6 traffic-filter', conf)
            acl_v6_config['afi'] = 'ipv6'
            acl_v6_config['acls'] = acls
            config['access_groups'].append(acl_v6_config)

        return utils.remove_empties(config)
