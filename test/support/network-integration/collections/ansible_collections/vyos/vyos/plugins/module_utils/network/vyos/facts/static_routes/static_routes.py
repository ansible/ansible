#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos static_routes fact class
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
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.argspec.static_routes.static_routes import (
    Static_routesArgs,
)
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.utils.utils import (
    get_route_type,
)


class Static_routesFacts(object):
    """ The vyos static_routes fact class
    """

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = Static_routesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection):
        return connection.get_config()

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for static_routes
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
        objs = []
        r_v4 = []
        r_v6 = []
        af = []
        static_routes = findall(
            r"set protocols static route(6)? (\S+)", data, M
        )
        if static_routes:
            for route in set(static_routes):
                route_regex = r" %s .+$" % route[1]
                cfg = findall(route_regex, data, M)
                sr = self.render_config(cfg)
                sr["dest"] = route[1].strip("'")
                afi = self.get_afi(sr["dest"])
                if afi == "ipv4":
                    r_v4.append(sr)
                else:
                    r_v6.append(sr)
            if r_v4:
                afi_v4 = {"afi": "ipv4", "routes": r_v4}
                af.append(afi_v4)
            if r_v6:
                afi_v6 = {"afi": "ipv6", "routes": r_v6}
                af.append(afi_v6)
            config = {"address_families": af}
            if config:
                objs.append(config)

        ansible_facts["ansible_network_resources"].pop("static_routes", None)
        facts = {}
        if objs:
            facts["static_routes"] = []
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["static_routes"].append(utils.remove_empties(cfg))

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
        next_hops_conf = "\n".join(filter(lambda x: ("next-hop" in x), conf))
        blackhole_conf = "\n".join(filter(lambda x: ("blackhole" in x), conf))
        routes_dict = {
            "blackhole_config": self.parse_blackhole(blackhole_conf),
            "next_hops": self.parse_next_hop(next_hops_conf),
        }
        return routes_dict

    def parse_blackhole(self, conf):
        blackhole = None
        if conf:
            distance = search(r"^.*blackhole distance (.\S+)", conf, M)
            bh = conf.find("blackhole")
            if distance is not None:
                blackhole = {}
                value = distance.group(1).strip("'")
                blackhole["distance"] = int(value)
            elif bh:
                blackhole = {}
                blackhole["type"] = "blackhole"
        return blackhole

    def get_afi(self, address):
        route_type = get_route_type(address)
        if route_type == "route":
            return "ipv4"
        elif route_type == "route6":
            return "ipv6"

    def parse_next_hop(self, conf):
        nh_list = None
        if conf:
            nh_list = []
            hop_list = findall(r"^.*next-hop (.+)", conf, M)
            if hop_list:
                for hop in hop_list:
                    distance = search(r"^.*distance (.\S+)", hop, M)
                    interface = search(r"^.*interface (.\S+)", hop, M)

                    dis = hop.find("disable")
                    hop_info = hop.split(" ")
                    nh_info = {
                        "forward_router_address": hop_info[0].strip("'")
                    }
                    if interface:
                        nh_info["interface"] = interface.group(1).strip("'")
                    if distance:
                        value = distance.group(1).strip("'")
                        nh_info["admin_distance"] = int(value)
                    elif dis >= 1:
                        nh_info["enabled"] = False
                    for element in nh_list:
                        if (
                            element["forward_router_address"]
                            == nh_info["forward_router_address"]
                        ):
                            if "interface" in nh_info.keys():
                                element["interface"] = nh_info["interface"]
                            if "admin_distance" in nh_info.keys():
                                element["admin_distance"] = nh_info[
                                    "admin_distance"
                                ]
                            if "enabled" in nh_info.keys():
                                element["enabled"] = nh_info["enabled"]
                            nh_info = None
                    if nh_info is not None:
                        nh_list.append(nh_info)
        return nh_list
