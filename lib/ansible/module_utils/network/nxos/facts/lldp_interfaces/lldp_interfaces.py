#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos lldp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.lldp_interfaces.lldp_interfaces import Lldp_interfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type


class Lldp_interfacesFacts(object):
    """ The nxos lldp_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lldp_interfacesArgs.argument_spec
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
        return connection.get('show running-config | section ^interface')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for lldp_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        objs = []

        data = data.split('interface')
        resources = []

        for i in range(len(data)):
            intf = data[i].split('\n')
            for l in range(1, len(intf)):
                if not re.search('lldp', intf[l]):
                    intf[l] = ''
            intf = list(filter(None, intf))
            intf = ''.join(i for i in intf)
            resources.append(intf)

        for resource in resources:
            if resource:  # and re.search(r'lldp', resource):
                obj = self.render_config(self.generated_spec, resource)
                if obj and len(obj.keys()) >= 1:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('lldp_interfaces', None)
        facts = {}
        if objs:
            facts['lldp_interfaces'] = []
            params = utils.validate_config(
                self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['lldp_interfaces'].append(utils.remove_empties(cfg))

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
        match = re.search(r'^ (\S+)', conf)
        if match is None:
            return {}
        intf = match.group(1)
        if get_interface_type(intf) not in ['management', 'ethernet']:
            return {}
        config['name'] = intf
        if 'lldp receive' in conf:  # for parsed state only
            config['receive'] = True
        if 'no lldp receive' in conf:
            config['receive'] = False

        if 'lldp transmit' in conf:  # for parsed state only
            config['transmit'] = True
        if 'no lldp transmit' in conf:
            config['transmit'] = False
        if 'management-address' in conf:
            config['tlv_set']['management_address'] = re.search(
                r'management-address (\S*)', conf).group(1)
        if 'vlan' in conf:
            config['tlv_set']['vlan'] = re.search(
                r'vlan (\S*)', conf).group(1)
        return utils.remove_empties(config)
