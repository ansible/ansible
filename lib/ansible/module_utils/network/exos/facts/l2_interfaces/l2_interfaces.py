#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.exos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.network.exos.exos import send_requests


class L2_interfacesFacts(object):
    """ The exos l2_interfaces fact class
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
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            request = [{
                "path": "/rest/restconf/data/openconfig-interfaces:interfaces",
                "method": "GET"
            }]
            data = send_requests(self._module, requests=request)

        objs = []
        if data:
            for d in data[0]["openconfig-interfaces:interfaces"]["interface"]:
                obj = self.render_config(self.generated_spec, d)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('l2_interfaces', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['l2_interfaces'] = params['config']

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
        if conf["config"]["type"] == "ethernetCsmacd":
            conf_dict = conf["openconfig-if-ethernet:ethernet"]["openconfig-vlan:switched-vlan"]["config"]
            config["name"] = conf["name"]
            if conf_dict["interface-mode"] == "ACCESS":
                config["access"]["vlan"] = conf_dict.get("access-vlan")
            else:
                if 'native-vlan' in conf_dict:
                    config["trunk"]["native_vlan"] = conf_dict.get("native-vlan")
                config["trunk"]["trunk_allowed_vlans"] = conf_dict.get("trunk-vlans")
        return utils.remove_empties(config)
