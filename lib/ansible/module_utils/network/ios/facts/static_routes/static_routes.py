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


from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.utils.utils import netmask_to_cidr
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

    def get_static_routes_data(self, connection):
        return connection.get('sh running-config | include ip route|ipv6 route')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for static_routes
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        objs = []
        if not data:
            data = self.get_static_routes_data(connection)
        # operate on a collection of resource x
        config = data.split('\n')

        same_dest = self.populate_destination(config)
        for key in same_dest.keys():
            if key:
                obj = self.render_config(self.generated_spec, key, same_dest[key])
                if obj:
                    objs.append(obj)
        facts = {}

        # append all static routes address_family with NO VRF together
        no_vrf_address_family = {
            'address_families': [each.get('address_families')[0] for each in objs if each.get('vrf') is None]
        }

        temp_objs = [each for each in objs if each.get('vrf') is not None]
        temp_objs.append(no_vrf_address_family)
        objs = temp_objs

        if objs:
            facts['static_routes'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['static_routes'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def update_netmask_to_cidr(self, filter, pos, del_pos):
        netmask = filter.split(' ')
        dest = netmask[pos] + '/' + netmask_to_cidr(netmask[del_pos])
        netmask[pos] = dest
        del netmask[del_pos]
        filter_vrf = ' '
        return filter_vrf.join(netmask), dest

    def populate_destination(self, config):
        same_dest = {}
        ip_str = ''
        for i in sorted(config):
            if i:
                if '::' in i and 'vrf' in i:
                    ip_str = 'ipv6 route vrf'
                elif '::' in i and 'vrf' not in i:
                    ip_str = 'ipv6 route'
                elif '.' in i and 'vrf' in i:
                    ip_str = 'ip route vrf'
                elif '.' in i and 'vrf' not in i:
                    ip_str = 'ip route'

                if 'vrf' in i:
                    filter_vrf = utils.parse_conf_arg(i, ip_str)
                    if '/' not in filter_vrf and '::' not in filter_vrf:
                        filter_vrf, dest_vrf = self.update_netmask_to_cidr(filter_vrf, 1, 2)
                        dest_vrf = dest_vrf + '_vrf'
                    else:
                        dest_vrf = filter_vrf.split(' ')[1]
                    if dest_vrf not in same_dest.keys():
                        same_dest[dest_vrf] = []
                        same_dest[dest_vrf].append('vrf ' + filter_vrf)
                    elif 'vrf' not in same_dest[dest_vrf][0]:
                        same_dest[dest_vrf] = []
                        same_dest[dest_vrf].append('vrf ' + filter_vrf)
                    else:
                        same_dest[dest_vrf].append(('vrf ' + filter_vrf))
                else:
                    filter = utils.parse_conf_arg(i, ip_str)
                    if '/' not in filter and '::' not in filter:
                        filter, dest = self.update_netmask_to_cidr(filter, 0, 1)
                    else:
                        dest = filter.split(' ')[0]
                    if dest not in same_dest.keys():
                        same_dest[dest] = []
                        same_dest[dest].append(filter)
                    elif 'vrf' in same_dest[dest][0]:
                        same_dest[dest] = []
                        same_dest[dest].append(filter)
                    else:
                        same_dest[dest].append(filter)
        return same_dest

    def render_config(self, spec, conf, conf_val):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['address_families'] = []
        route_dict = dict()
        final_route = dict()
        afi = dict()
        final_route['routes'] = []
        next_hops = []
        hops = {}
        vrf = ''
        address_family = dict()
        for each in conf_val:
            route = each.split(' ')
            if 'vrf' in conf_val[0]:
                vrf = route[route.index('vrf') + 1]
                route_dict['dest'] = conf.split('_')[0]
            else:
                route_dict['dest'] = conf
            if 'vrf' in conf_val[0]:
                hops = {}
                if '::' in conf:
                    hops['forward_router_address'] = route[3]
                    afi['afi'] = 'ipv6'
                elif '.' in conf:
                    hops['forward_router_address'] = route[3]
                    afi['afi'] = "ipv4"
                else:
                    hops['interface'] = conf
            else:

                if '::' in conf:
                    hops['forward_router_address'] = route[1]
                    afi['afi'] = 'ipv6'
                elif '.' in conf:
                    hops['forward_router_address'] = route[1]
                    afi['afi'] = "ipv4"
                else:
                    hops['interface'] = route[1]
            try:
                temp_list = each.split(' ')
                if 'tag' in temp_list:
                    del temp_list[temp_list.index('tag') + 1]
                if 'track' in temp_list:
                    del temp_list[temp_list.index('track') + 1]
                # find distance metric
                dist_metrics = int(
                    [i for i in temp_list if '.' not in i and ':' not in i and ord(i[0]) > 48 and ord(i[0]) < 57][0]
                )
            except IndexError:
                dist_metrics = None
            if dist_metrics:
                hops['distance_metric'] = dist_metrics
            if 'name' in route:
                hops['name'] = route[route.index('name') + 1]
            if 'multicast' in route:
                hops['multicast'] = True
            if 'dhcp' in route:
                hops['dhcp'] = True
            if 'global' in route:
                hops['global'] = True
            if 'permanent' in route:
                hops['permanent'] = True
            if 'tag' in route:
                hops['tag'] = route[route.index('tag') + 1]
            if 'track' in route:
                hops['track'] = route[route.index('track') + 1]
            next_hops.append(hops)
            hops = {}
        route_dict['next_hops'] = next_hops
        if route_dict:
            final_route['routes'].append(route_dict)
        address_family.update(afi)
        address_family.update(final_route)
        config['address_families'].append(address_family)
        if vrf:
            config['vrf'] = vrf

        return utils.remove_empties(config)
