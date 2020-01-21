#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos guest_virtual_machines fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.exos.argspec.guest_virtual_machines.guest_virtual_machines import Guest_virtual_machinesArgs
from ansible.module_utils.network.exos.exos import send_requests


class Guest_virtual_machinesFacts(object):
    """ The exos guest_virtual_machines fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Guest_virtual_machinesArgs.argument_spec
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
        """ Populate the facts for guest_virtual_machines
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            requests = [
                {
                    "path": "/rest/restconf/data/extreme-virtual-service:virtual-services-config/",
                    "method": "GET"
                },
                {
                    "path": "/rest/restconf/data/extreme-virtual-service:virtual-services-state/",
                    "method": "GET"
                }
            ]

            data = send_requests(self._module, requests=requests)

        objs = []
        if data:
            obj = self.render_config(self.generated_spec, data)
            if obj:
                objs.extend(obj)

        ansible_facts['ansible_network_resources'].pop('guest_virtual_machines', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['guest_virtual_machines'] = params['config']

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

        vms = []
        conf_config = conf[0]["extreme-virtual-service:virtual-services-config"]
        conf_state = conf[1]["extreme-virtual-service:virtual-services-state"]
        if conf_config.get("virtual-service-config") and conf_state.get("virtual-service-state"):
            conf_config = conf_config["virtual-service-config"]
            conf_state = conf_state["virtual-service-state"]
            for d in range(len(conf_config)):
                config["auto_start"] = conf_config[d]["enable"]
                config["image"] = conf_state[d]["package-info"]["path"] + str('/') + conf_state[d]["package-info"]["name"]
                config["memory_size"] = conf_config[d]["memory-size"]
                config["name"] = conf_config[d]["name"]
                config["num_cores"] = conf_config[d]["num-cores"]
                config["operational_state"] = "started" if conf_state[d]["state"]["state"] == 1 else "stopped"
                config["virtual_ports"] = []
                if conf_config[d].get("vports"):
                    conf_vport = conf_config[d]["vports"]["vport"]
                    for num in range(len(conf_config[d]["vports"]["vport"])):
                        config_vport = {}
                        config_vport["name"] = conf_vport[num].get("name")
                        config_vport["type"] = conf_vport[num].get("connect-type").lower()
                        config_vport["port"] = conf_vport[num].get("port")
                        if conf_vport[num].get("vlans"):
                            config_vport["vlan_id"] = conf_vport[num]["vlans"]["vlan"][0]["id"]
                        config["virtual_ports"].append(config_vport)
                config["vnc"]["enabled"] = False if conf_config[d]["vnc-port"] == 0 else True
                config["vnc"]["port"] = conf_config[d]["vnc-port"]
                vms.append(utils.remove_empties(config))
        return vms
