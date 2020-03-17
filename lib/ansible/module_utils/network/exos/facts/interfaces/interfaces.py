#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import json
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.exos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network.exos.exos import send_requests, run_commands


class InterfacesFacts(object):
    """ The exos interfaces fact class
    """

    PORT_SPEED = {
        "0": "AUTO",
        "1": "SPEED_10MB",
        "2": "SPEED_100MB",
        "3": "SPEED_1GB",
        "4": "SPEED_10GB",
        "5": "SPEED_25GB",
        "6": "SPEED_40GB",
        "7": "SPEED_50GB",
        "8": "SPEED_100GB"
    }

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = InterfacesArgs.argument_spec
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
        """ Populate the facts for interfaces
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

        ansible_facts['ansible_network_resources'].pop('interfaces', None)
        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['interfaces'] = params['config']

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
        if conf["config"]["type"] == "ethernetCsmacd" and conf["state"]["oper-status"] == "DOWN":
            config["name"] = conf["name"]
            config["description"] = conf["config"]["description"]
            config["enabled"] = conf["config"]["enabled"]
            dic = [{"command": 'debug cfgmgr show next vlan.show_ports_info_detail portList=' + conf["name"], "output": "json"}]
            conf_json = run_commands(self._module, commands=dic)
            config["jumbo_frames"]["enabled"] = True if conf_json[0]["data"][0]["isJumboEnabled"] == "1" else False
            if conf_json[0]["data"][0]["duplexSpeedCfg"] == "1":
                config["duplex"] = "FULL"
            elif conf_json[0]["data"][0]["duplexSpeedCfg"] == "2":
                config["duplex"] = "AUTO"
            else:
                config["duplex"] = "HALF"
            if conf_json[0]["data"][0]["portSpeedCfg"] in self.PORT_SPEED.keys():
                config["speed"] = self.PORT_SPEED[conf_json[0]["data"][0]["portSpeedCfg"]]
            else:
                config["speed"] = "SPEED_UNKNOWN"
        return utils.remove_empties(config)
