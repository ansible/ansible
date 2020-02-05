#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
The nxos bfd_interfaces fact class
Populate the facts tree based on the current device configuration.
"""
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.bfd_interfaces.bfd_interfaces import Bfd_interfacesArgs
from ansible.module_utils.network.nxos.utils.utils import get_interface_type


class Bfd_interfacesFacts(object):
    """ The nxos_bfd_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Bfd_interfacesArgs.argument_spec
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
        """ Populate the facts for bfd_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []

        if not data:
            data = connection.get("show running-config | section '^interface|^feature bfd'")

        # Some of the bfd attributes
        if 'feature bfd' in data.split('\n'):
            resources = data.split('interface ')
            resources.pop(0)
        else:
            resources = []
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj and len(obj.keys()) > 1:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('bfd_interfaces', None)
        facts = {}
        if objs:
            facts['bfd_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['bfd_interfaces'].append(utils.remove_empties(cfg))

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
        # 'bfd'/'bfd echo' do not nvgen when enabled thus set to 'enable' when None.
        # 'bfd' is not supported on some platforms
        config['bfd'] = utils.parse_conf_cmd_arg(conf, 'bfd', 'enable', 'disable') or 'enable'
        config['echo'] = utils.parse_conf_cmd_arg(conf, 'bfd echo', 'enable', 'disable') or 'enable'

        return utils.remove_empties(config)
