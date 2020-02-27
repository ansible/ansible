#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr static_routes fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import re
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.argspec.static_routes.static_routes import Static_routesArgs


class Static_routesFacts(object):
    """ The iosxr static_routes fact class
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
        return connection.get_config(flags="router static")

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

        objs = []

        if "No such configuration" not in data:
            for entry in re.compile(r"(\s) vrf").split(data):
                obj = self.render_config(self.generated_spec, entry)
                if obj:
                    objs.append(obj)

        ansible_facts["ansible_network_resources"].pop("static_routes", None)
        facts = {}

        facts["static_routes"] = []
        params = utils.validate_config(self.argument_spec, {"config": objs})
        for cfg in params["config"]:
            facts["static_routes"].append(utils.remove_empties(cfg))

        ansible_facts["ansible_network_resources"].update(facts)
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
        entry_list = conf.split(" address-family")
        config["address_families"] = []

        if "router static" not in entry_list[0]:
            config["vrf"] = entry_list[0].replace("!", "").strip()

        for item in entry_list[1:]:
            routes = []
            address_family = {"routes": []}
            address_family["afi"], address_family["safi"] = self.parse_af(item)

            destinations = re.findall(r"((?:\S+)/(?:\d+)) (?:.*)", item, re.M)
            for dest in set(destinations):
                route = {"next_hops": []}
                route["dest"] = dest

                regex = r"%s .+$" % dest
                cfg = re.findall(regex, item, re.M)

                for route_entry in cfg:
                    exit_point = {}
                    exit_point["forward_router_address"] = self.parse_faddr(route_entry)
                    exit_point["interface"] = self.parse_intf(route_entry)
                    exit_point["admin_distance"] = self.parse_admin_distance(route_entry)

                    for x in [
                        "tag",
                        "tunnel-id",
                        "metric",
                        "description",
                        "track",
                        "vrflabel",
                        "dest_vrf",
                    ]:
                        exit_point[x.replace("-", "_")] = self.parse_attrib(
                            route_entry, x.replace("dest_vrf", "vrf")
                        )

                    route["next_hops"].append(exit_point)

                routes.append(route)
                address_family["routes"] = sorted(routes, key=lambda i: i["dest"])
            config["address_families"].append(address_family)

        return utils.remove_empties(config)

    def parse_af(self, item):
        match = re.search(r"(?:\s*)(\w+)(?:\s*)(\w+)", item, re.M)
        if match:
            return match.group(1), match.group(2)

    def parse_faddr(self, item):
        for x in item.split(" "):
            if (":" in x or "." in x) and "/" not in x:
                return x

    def parse_intf(self, item):
        match = re.search(r" ((\w+)((?:\d)/(?:\d)/(?:\d)/(?:\d+)))", item)
        if match:
            return match.group(1)

    def parse_attrib(self, item, attrib):
        match = re.search(r" %s (\S+)" % attrib, item)
        if match:
            val = match.group(1).strip("'")
            if attrib in ["tunnel-id", "vrflabel", "tag", "metric"]:
                val = int(val)
            return val

    def parse_admin_distance(self, item):
        split_item = item.split(" ")
        for item in [
            "vrf",
            "metric",
            "tunnel-id",
            "vrflabel",
            "track",
            "tag",
            "description",
        ]:
            try:
                del split_item[split_item.index(item) + 1]
                del split_item[split_item.index(item)]
            except ValueError:
                continue
        try:
            return [
                i for i in split_item if "." not in i and ":" not in i and ord(i[0]) > 48 and ord(i[0]) < 57
            ][0]
        except IndexError:
            return None
