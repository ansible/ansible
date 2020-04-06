#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import re
from copy import deepcopy
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible.module_utils.six import iteritems
from ansible_collections.ansible.netcommon.plugins.module_utils.compat import (
    ipaddress,
)
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.argspec.l3_interfaces.l3_interfaces import (
    L3_interfacesArgs,
)


class L3_interfacesFacts(object):
    """ The vyos l3_interfaces fact class
    """

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = L3_interfacesArgs.argument_spec
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
        """ Populate the facts for l3_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get_config()

        # operate on a collection of resource x
        objs = []
        interface_names = re.findall(
            r"set interfaces (?:ethernet|bonding|vti|vxlan) (?:\'*)(\S+)(?:\'*)",
            data,
            re.M,
        )
        if interface_names:
            for interface in set(interface_names):
                intf_regex = r" %s .+$" % interface
                cfg = re.findall(intf_regex, data, re.M)
                obj = self.render_config(cfg)
                obj["name"] = interface.strip("'")
                if obj:
                    objs.append(obj)

        ansible_facts["ansible_network_resources"].pop("l3_interfaces", None)
        facts = {}
        if objs:
            facts["l3_interfaces"] = []
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["l3_interfaces"].append(utils.remove_empties(cfg))

        ansible_facts["ansible_network_resources"].update(facts)
        return ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        vif_conf = "\n".join(filter(lambda x: ("vif" in x), conf))
        eth_conf = "\n".join(filter(lambda x: ("vif" not in x), conf))
        config = self.parse_attribs(eth_conf)
        config["vifs"] = self.parse_vifs(vif_conf)

        return utils.remove_empties(config)

    def parse_vifs(self, conf):
        vif_names = re.findall(r"vif (\d+)", conf, re.M)
        vifs_list = None
        if vif_names:
            vifs_list = []
            for vif in set(vif_names):
                vif_regex = r" %s .+$" % vif
                cfg = "\n".join(re.findall(vif_regex, conf, re.M))
                obj = self.parse_attribs(cfg)
                obj["vlan_id"] = vif
                if obj:
                    vifs_list.append(obj)

        return vifs_list

    def parse_attribs(self, conf):
        config = {}
        ipaddrs = re.findall(r"address (\S+)", conf, re.M)
        config["ipv4"] = []
        config["ipv6"] = []

        for item in ipaddrs:
            item = item.strip("'")
            if item == "dhcp":
                config["ipv4"].append({"address": item})
            elif item == "dhcpv6":
                config["ipv6"].append({"address": item})
            else:
                ip_version = ipaddress.ip_address(item.split("/")[0]).version
                if ip_version == 4:
                    config["ipv4"].append({"address": item})
                else:
                    config["ipv6"].append({"address": item})

        for key, value in iteritems(config):
            if value == []:
                config[key] = None

        return utils.remove_empties(config)
