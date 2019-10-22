# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import re

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs


class L2_interfacesFacts(object):
    """ The eos l2_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L2_interfacesArgs.argument_spec
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

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected configuration
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get('show running-config | section ^interface')

        # operate on a collection of resource x
        config = data.split('interface ')
        objs = []
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['l2_interfaces'] = [utils.remove_empties(cfg) for cfg in params['config']]
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

        # populate the facts from the configuration
        config['name'] = re.match(r'(\S+)', conf).group(1).replace('"', '')

        has_access = re.search(r"switchport access vlan (\d+)", conf)
        if has_access:
            config["access"] = {"vlan": int(has_access.group(1))}

        has_trunk = re.findall(r"switchport trunk (.+)", conf)
        if has_trunk:
            trunk = {}
            for match in has_trunk:
                has_native = re.match(r"native vlan (\d+)", match)
                if has_native:
                    trunk["native_vlan"] = int(has_native.group(1))
                    continue

                has_allowed = re.match(r"allowed vlan (\S+)", match)
                if has_allowed:
                    # TODO: listify?
                    trunk["trunk_allowed_vlans"] = has_allowed.group(1)
                    continue
            config['trunk'] = trunk

        return utils.remove_empties(config)
