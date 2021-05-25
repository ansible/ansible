#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos lag_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type
from re import findall, search, M
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.argspec.lag_interfaces.lag_interfaces import (
    Lag_interfacesArgs,
)


class Lag_interfacesFacts(object):
    """ The vyos lag_interfaces fact class
    """

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = Lag_interfacesArgs.argument_spec
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
        """ Populate the facts for lag_interfaces
        :param module: the module instance
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get_config()

        objs = []
        lag_names = findall(r"^set interfaces bonding (\S+)", data, M)
        if lag_names:
            for lag in set(lag_names):
                lag_regex = r" %s .+$" % lag
                cfg = findall(lag_regex, data, M)
                obj = self.render_config(cfg)

                output = connection.run_commands(
                    ["show interfaces bonding " + lag + " slaves"]
                )
                lines = output[0].splitlines()
                members = []
                member = {}
                if len(lines) > 1:
                    for line in lines[2:]:
                        splitted_line = line.split()

                        if len(splitted_line) > 1:
                            member["member"] = splitted_line[0]
                            members.append(member)
                        else:
                            members = []
                        member = {}
                obj["name"] = lag.strip("'")
                if members:
                    obj["members"] = members

                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts["lag_interfaces"] = []
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["lag_interfaces"].append(utils.remove_empties(cfg))

        ansible_facts["ansible_network_resources"].update(facts)
        return ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        arp_monitor_conf = "\n".join(
            filter(lambda x: ("arp-monitor" in x), conf)
        )
        hash_policy_conf = "\n".join(
            filter(lambda x: ("hash-policy" in x), conf)
        )
        lag_conf = "\n".join(filter(lambda x: ("bond" in x), conf))
        config = self.parse_attribs(["mode", "primary"], lag_conf)
        config["arp_monitor"] = self.parse_arp_monitor(arp_monitor_conf)
        config["hash_policy"] = self.parse_hash_policy(hash_policy_conf)

        return utils.remove_empties(config)

    def parse_attribs(self, attribs, conf):
        config = {}
        for item in attribs:
            value = utils.parse_conf_arg(conf, item)
            if value:
                config[item] = value.strip("'")
            else:
                config[item] = None
        return utils.remove_empties(config)

    def parse_arp_monitor(self, conf):
        arp_monitor = None
        if conf:
            arp_monitor = {}
            target_list = []
            interval = search(r"^.*arp-monitor interval (.+)", conf, M)
            targets = findall(r"^.*arp-monitor target '(.+)'", conf, M)
            if targets:
                for target in targets:
                    target_list.append(target)
                arp_monitor["target"] = target_list
            if interval:
                value = interval.group(1).strip("'")
                arp_monitor["interval"] = int(value)
        return arp_monitor

    def parse_hash_policy(self, conf):
        hash_policy = None
        if conf:
            hash_policy = search(r"^.*hash-policy (.+)", conf, M)
            hash_policy = hash_policy.group(1).strip("'")
        return hash_policy
