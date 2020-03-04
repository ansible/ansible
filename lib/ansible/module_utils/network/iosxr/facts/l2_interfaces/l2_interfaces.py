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
from ansible.module_utils.network.iosxr.utils.utils import get_interface_type
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

    def populate_facts(self, connection, ansible_facts, data=None):
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

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

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

        intf = match.group(1)

        if match.group(1).lower() == "preconfigure":
            match = re.search(r'^(\S+) (.*)', conf)
            if match:
                intf = match.group(2)

        if get_interface_type(intf) == 'unknown':
            return {}

        if intf.lower().startswith('gi'):
            config['name'] = intf

            # populate the facts from the configuration
            native_vlan = re.search(r"dot1q native vlan (\d+)", conf)
            if native_vlan:
                config["native_vlan"] = int(native_vlan.group(1))

            dot1q = utils.parse_conf_arg(conf, 'encapsulation dot1q')
            config['q_vlan'] = []
            if dot1q:
                config['q_vlan'].append(int(dot1q.split(' ')[0]))
                if len(dot1q.split(' ')) > 1:
                    config['q_vlan'].append(int(dot1q.split(' ')[2]))

            if utils.parse_conf_cmd_arg(conf, 'l2transport', True):
                config['l2transport'] = True
            if utils.parse_conf_arg(conf, 'propagate'):
                config['propagate'] = True
            config['l2protocol'] = []

            cdp = utils.parse_conf_arg(conf, 'l2protocol cdp')
            pvst = utils.parse_conf_arg(conf, 'l2protocol pvst')
            stp = utils.parse_conf_arg(conf, 'l2protocol stp')
            vtp = utils.parse_conf_arg(conf, 'l2protocol vtp')
            if cdp:
                config['l2protocol'].append({'cdp': cdp})
            if pvst:
                config['l2protocol'].append({'pvst': pvst})
            if stp:
                config['l2protocol'].append({'stp': stp})
            if vtp:
                config['l2protocol'].append({'vtp': vtp})

            return utils.remove_empties(config)
