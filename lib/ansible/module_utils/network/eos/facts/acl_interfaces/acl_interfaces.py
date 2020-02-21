#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos acl_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.acl_interfaces.acl_interfaces import Acl_interfacesArgs


class Acl_interfacesFacts(object):
    """ The eos acl_interfaces fact class
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

    def get_device_data(self, connection):
        return connection.get('show running-config | include interface | access-group | traffic-filter')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for acl_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = self.get_device_data(connection)
        # split the config into instances of the resource
        resource_delim = 'interface'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern,
                                                   data,
                                                   re.DOTALL)]
        objs = []
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('acl_interfaces', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['acl_interfaces'] = [utils.remove_empties(cfg) for cfg in params['config']]

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
        access_group_list = []
        access_group_v6_list = []
        acls_list = []
        group_list = []
        group_dict = {}
        config['name'] = utils.parse_conf_arg(conf, 'interface')
        conf_lines = conf.split('\n')
        for line in conf_lines:
            if config['name'] in line:
                continue
            access_group = utils.parse_conf_arg(line, 'ip access-group')
            # This module was verified on an ios device since vEOS doesnot support
            # acl_interfaces cnfiguration. In ios, ipv6 acl is configured as
            # traffic-filter and in eos it is access-group

            # access_group_v6 = utils.parse_conf_arg(line, 'ipv6 traffic-filter')
            access_group_v6 = utils.parse_conf_arg(line, 'ipv6 access-group')
            if access_group:
                access_group_list.append(access_group)
            if access_group_v6:
                access_group_v6_list.append(access_group_v6)
        if access_group_list:
            for acl in access_group_list:
                a_name = acl.split()[0]
                a_dir = acl.split()[1]
                acls_dict = {"name": a_name, "direction": a_dir}
                acls_list.append(acls_dict)
            group_dict = {"afi": "ipv4", "acls": acls_list}
            group_list.append(group_dict)
            acls_list = []
        if group_list:
            config['access_groups'] = group_list
        if access_group_v6_list:
            for acl in access_group_v6_list:
                a_name = acl.split()[0]
                a_dir = acl.split()[1]
                acls_dict = {"name": a_name, "direction": a_dir}
                acls_list.append(acls_dict)
            group_dict = {"acls": acls_list, "afi": "ipv6"}
            group_list.append(group_dict)
            acls_list = []
        if group_list:
            config['access_groups'] = group_list
        return utils.remove_empties(config)
