#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus lldp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.argspec.lldp_interfaces.lldp_interfaces import Lldp_interfacesArgs
from ansible.module_utils.network.awplus.utils.utils import get_interface_type, normalize_interface


class Lldp_interfacesFacts(object):
    """ The awplus lldp_interfaces fact class
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

    def get_lldp_facts(self, connection):
        return connection.get('show lldp interface')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for lldp_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:
            pass

        objs = []
        if not data:
            data = self.get_lldp_facts(connection)
        # operate on a collection of resource x
        config = data.split('\n')

        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
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
        match = re.search(r'(\d+\.\d+\.\d+).+', conf, re.M)
        intf = ''
        if match:
            intf = match.group(1)

        if get_interface_type(intf) == 'unknown':
            return {}

        if intf.lower()[0].isdigit():
            config['name'] = normalize_interface(intf)

            if 'Rx' in conf:
                config['receive'] = True
            else:
                config['receive'] = False

            if 'Tx' in conf:
                config['transmit'] = True
            else:
                config['transmit'] = False

        return utils.remove_empties(config)
