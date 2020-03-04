#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos static_routes fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.static_routes.static_routes import Static_routesArgs


class Static_routesFacts(object):
    """ The eos static_routes fact class
    """

    def __init__(self, module, subspec='config', options='options'):
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
        return connection.get('show running-config | grep route')

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

        # split the config into instances of the resource
        resource_delim = 'ip.* route'
        find_pattern = r'(?:^|\n)%s.*?(?=(?:^|\n)%s|$)' % (resource_delim,
                                                           resource_delim)
        resources = [p.strip() for p in re.findall(find_pattern, data)]
        resources_without_vrf = []
        resource_vrf = {}
        for resource in resources:
            if resource and "vrf" not in resource:
                resources_without_vrf.append(resource)
            else:
                vrf = re.search(r'ip(v6)* route vrf (.*?) .*', resource)
                if vrf.group(2) in resource_vrf.keys():
                    vrf_val = resource_vrf[vrf.group(2)]
                    vrf_val.append(resource)
                    resource_vrf.update({vrf.group(2): vrf_val})
                else:
                    resource_vrf.update({vrf.group(2): [resource]})
        resources_without_vrf = ["\n".join(resources_without_vrf)]
        for vrf in resource_vrf.keys():
            vrflist = ["\n".join(resource_vrf[vrf])]
            resource_vrf.update({vrf: vrflist})
        objs = []
        for resource in resources_without_vrf:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        for resource in resource_vrf.keys():
            if resource:
                obj = self.render_config(self.generated_spec, resource_vrf[resource][0])
                if obj:
                    objs.append(obj)
        ansible_facts['ansible_network_resources'].pop('static_routes', None)
        facts = {}
        if objs:
            facts['static_routes'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['static_routes'].append(utils.remove_empties(cfg))
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
        address_family_dict = {}
        route_dict = {}
        dest_list = []
        afi_list = []
        vrf_list = []
        routes = []
        config["address_families"] = []
        next_hops = {}
        interface_list = ["Ethernet", "Loopback", "Management",
                          "Port-Channel", "Tunnel", "Vlan", "Vxlan", "vtep"]
        conf_list = conf.split('\n')
        for conf_elem in conf_list:
            matches = re.findall(r'(ip|ipv6) route ([\d\.\/:]+|vrf) (.+)$', conf_elem)
            if matches:
                remainder = matches[0][2].split()
                route_update = False
                if matches[0][1] == "vrf":
                    vrf = remainder.pop(0)
                    # new vrf
                    if vrf not in vrf_list and vrf_list:
                        route_dict.update({"next_hops": next_hops})
                        routes.append(route_dict)
                        address_family_dict.update({"routes": routes})
                        config["address_families"].append(address_family_dict)
                        route_update = True
                    config.update({"vrf": vrf})
                    vrf_list.append(vrf)
                    dest = remainder.pop(0)
                else:
                    config["vrf"] = None
                    dest = matches[0][1]
                afi = "ipv4" if matches[0][0] == "ip" else "ipv6"
                if afi not in afi_list:
                    if afi_list and not route_update:
                        # new afi and not the first updating all prev configs
                        route_dict.update({"next_hops": next_hops})
                        routes.append(route_dict)
                        address_family_dict.update({"routes": routes})
                        config["address_families"].append(address_family_dict)
                        route_update = True
                    address_family_dict = {}
                    address_family_dict.update({"afi": afi})
                    routes = []
                    afi_list.append(afi)
                # To check the format of the dest
                prefix = re.search(r'/', dest)
                if not prefix:
                    dest = dest + ' ' + remainder.pop(0)
                if dest not in dest_list:
                    # For new dest and  not the first dest
                    if dest_list and not route_update:
                        route_dict.update({"next_hops": next_hops})
                        routes.append(route_dict)
                    dest_list.append(dest)
                    next_hops = []
                    route_dict = {}
                    route_dict.update({"dest": dest})
                nexthops = {}
                nxthop_addr = re.search(r'[\.\:]', remainder[0])
                if nxthop_addr:
                    nexthops.update({"interface": remainder.pop(0)})
                    if remainder and remainder[0] == "label":
                        nexthops.update({"mpls_label": remainder.pop(1)})
                        remainder.pop(0)
                elif re.search(r'Nexthop-Group', remainder[0]):
                    nexthops.update({"nexthop_grp": remainder.pop(1)})
                    remainder.pop(0)
                else:
                    interface = remainder.pop(0)
                    if interface in interface_list:
                        interface = interface + " " + remainder.pop(0)
                    nexthops.update({"interface": interface})
                for attribute in remainder:
                    forward_addr = re.search(r'([\dA-Fa-f]+[:\.]+)+[\dA-Fa-f]+', attribute)
                    if forward_addr:
                        nexthops.update({"forward_router_address": remainder.pop(remainder.index(attribute))})
                for attribute in remainder:
                    for params in ["tag", "name", "track"]:
                        if attribute == params:
                            keyname = params
                            if attribute == "name":
                                keyname = "description"
                            nexthops.update({keyname: remainder.pop(remainder.index(attribute) + 1)})
                            remainder.pop(remainder.index(attribute))
                if remainder:
                    metric = re.search(r'\d+', remainder[0])
                    if metric:
                        nexthops.update({"admin_distance": remainder.pop(0)})
                next_hops.append(nexthops)
        route_dict.update({"next_hops": next_hops})
        routes.append(route_dict)
        address_family_dict.update({"routes": routes})
        config["address_families"].append(address_family_dict)
        return utils.remove_empties(config)
