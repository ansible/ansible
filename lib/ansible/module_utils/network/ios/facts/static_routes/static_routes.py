#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_static_routes fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.utils.utils import get_interface_type, normalize_interface
from ansible.module_utils.network.ios.argspec.static_routes.static_routes import Static_RoutesArgs


class Static_RoutesFacts(object):
    """ The ios_static_routes fact class
    """

    def __init__(self, module, subspec='config', options='options'):

        self._module = module
        self.argument_spec = Static_RoutesArgs.argument_spec
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
        """ Populate the facts for static_routes
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:
            pass

        objs = []
        if not data:
            data = connection.get('sh running-config | section ^ip route|ipv6 route')
        # operate on a collection of resource x
        config = data.split('\n')

        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)
        facts = {}

        if objs:
            facts['static_routes'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['static_routes'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def check_params(self, route, afi, final_route, vrf=False):
        route_dict = dict()
        if 'ipv4' in afi.values():
            if vrf:
                route_dict['dest'] = route[1] + ' ' + route[2]
            else:
                route_dict['dest'] = route[0] + ' ' + route[1]
        if 'ipv6' in afi.values():
            if vrf:
                route_dict['dest'] = route[1]
            else:
                route_dict['dest'] = route[0]
        if vrf:
            next_hops = []
            hops = {}
            if '.' in route[3]:
                hops['forward_router_address'] = route[3]
            elif '::' in route[3]:
                hops['forward_router_address'] = route[3]
            else:
                hops['interface'] = route[3]
            next_hops.append(hops)
            route_dict['next_hops'] = next_hops
        else:
            next_hops = []
            hops = {}
            if '.' in route[2]:
                hops['forward_router_address'] = route[2]
            elif '::' in route[1]:
                hops['forward_router_address'] = route[1]
            else:
                hops['interface'] = route[2]
            next_hops.append(hops)
            route_dict['next_hops'] = next_hops
        if 'name' in route:
            route_dict['name'] = route[route.index('name') + 1]
        if 'multicast' in route:
            route_dict['multicast'] = True
        if 'dhcp' in route:
            route_dict['dhcp'] = True
        if 'global' in route:
            route_dict['global'] = True
        if 'permanent' in route:
            route_dict['permanent'] = True
        if 'tag' in route:
            route_dict['tag'] = route[route.index('tag') + 1]
        if 'track' in route:
            route_dict['track'] = route[route.index('track') + 1]
        if route_dict:
            final_route['routes'].append(route_dict)

        return final_route

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

        if 'vrf' in conf:
            if 'ipv6' in conf:
                route_ipv6 = utils.parse_conf_arg(conf, 'ipv6 route vrf')
                vrf_ipv6 = route_ipv6.split(' ')[0]
                config['vrf'] = vrf_ipv6
                route_ipv4 = ''
            else:
                route_ipv4 = utils.parse_conf_arg(conf, 'ip route vrf')
                vrf_ipv4 = route_ipv4.split(' ')[0]
                config['vrf'] = vrf_ipv4
        else:
            if 'ipv6' in conf:
                route_ipv6 = utils.parse_conf_arg(conf, 'ipv6 route')
                route_ipv4 = vrf_ipv6 = None
            else:
                route_ipv4 = utils.parse_conf_arg(conf, 'ip route')
                vrf_ipv4 = None

        config['address_families'] = []
        address_family = dict()
        afi = dict()
        routes = dict()
        if route_ipv4:
            routes['routes'] = []
            afi['afi'] = 'ipv4'
            route_ipv4 = route_ipv4.split(' ')
            if vrf_ipv4:
                routes = self.check_params(route_ipv4, afi, routes, True)
            else:
                routes = self.check_params(route_ipv4, afi, routes)
            address_family.update(afi)
            address_family.update(routes)
        elif route_ipv6:
            routes['routes'] = []
            afi['afi'] = 'ipv6'
            route_ipv6 = route_ipv6.split(' ')
            if vrf_ipv6:
                routes = self.check_params(route_ipv6, afi, routes, True)
            else:
                routes = self.check_params(route_ipv6, afi, routes)
            address_family.update(afi)
            address_family.update(routes)

        config['address_families'].append(address_family)

        return utils.remove_empties(config)
