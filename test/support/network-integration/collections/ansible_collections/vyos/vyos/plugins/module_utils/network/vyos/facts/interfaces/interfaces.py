#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from re import findall, M
from copy import deepcopy
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.argspec.interfaces.interfaces import (
    InterfacesArgs,
)


class InterfacesFacts(object):
    """ The vyos interfaces fact class
    """

    def __init__(self, module, subspec="config", options="options"):
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
            data = connection.get_config(flags=["| grep interfaces"])

        objs = []
        interface_names = findall(
            r"^set interfaces (?:ethernet|bonding|vti|loopback|vxlan) (?:\'*)(\S+)(?:\'*)",
            data,
            M,
        )
        if interface_names:
            for interface in set(interface_names):
                intf_regex = r" %s .+$" % interface.strip("'")
                cfg = findall(intf_regex, data, M)
                obj = self.render_config(cfg)
                obj["name"] = interface.strip("'")
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts["interfaces"] = []
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["interfaces"].append(utils.remove_empties(cfg))

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
        vif_conf = "\n".join(filter(lambda x: ("vif" in x), conf))
        eth_conf = "\n".join(filter(lambda x: ("vif" not in x), conf))
        config = self.parse_attribs(
            ["description", "speed", "mtu", "duplex"], eth_conf
        )
        config["vifs"] = self.parse_vifs(vif_conf)

        return utils.remove_empties(config)

    def parse_vifs(self, conf):
        vif_names = findall(r"vif (?:\'*)(\d+)(?:\'*)", conf, M)
        vifs_list = None

        if vif_names:
            vifs_list = []
            for vif in set(vif_names):
                vif_regex = r" %s .+$" % vif
                cfg = "\n".join(findall(vif_regex, conf, M))
                obj = self.parse_attribs(["description", "mtu"], cfg)
                obj["vlan_id"] = int(vif)
                if obj:
                    vifs_list.append(obj)
            vifs_list = sorted(vifs_list, key=lambda i: i["vlan_id"])

        return vifs_list

    def parse_attribs(self, attribs, conf):
        config = {}
        for item in attribs:
            value = utils.parse_conf_arg(conf, item)
            if value and item == "mtu":
                config[item] = int(value.strip("'"))
            elif value:
                config[item] = value.strip("'")
            else:
                config[item] = None
        if "disable" in conf:
            config["enabled"] = False
        else:
            config["enabled"] = True

        return utils.remove_empties(config)
