#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_routes
version_added: "2.10"
author: "Anas Shami (@anass)"
short_description: Configure ip routes module
description:
  - This module provides declarative management of ip routes
    on Mellanox ONYX network devices.
notes:
options:
    multicasting:
        description:
            - Enable multicast routing on one vrf or all vrfs
        type: bool
        default: False
    route_type:
        description:
            - Specify the type of routing
        choices: ['default', 'multicast']
    vrf_name:
        description:
            - Static route or multicast this vrf
        type: str
    network_prefix:
        description:
            - The current network prefix eg: 1.1.1.1
        type: str
    netmask:
        description:
            - Set the netmask/netmask length for the network prefix eg: 255.255.255.0 or /24
        type: str
    nexthop:
        description:
            - The next hop in static route eg: 2.2.2.2.
        type: str
    routing:
        description:
            - Enable ip routing feature
        type: bool
    hostname_map:
        description:
            - Ensure a static host mapping for current hostname
        type: bool
    hostname:
        description:
            - Configure static hostname/IPv4 address mappings
        type: str
    hostip:
        description:
            - Configure ipv4 address using a hostname alias.
        type: str
    hostname_remove:
        description:
            - Remove static hostname/IPv4 address mappings
        type: bool
        default: False
    route_enable:
        description:
            - Enable/Disable routing.
        type: bool
        default: True
    domain:
        description:
            - Add a domain name to use when resolving hostnames
        type: str
    domain_remove:
        description:
            - Remove domain name
        type: str
        default: False
    mroute_preference:
        description:
            - Assign multicast route prefernce (1-255)
        type: int
    route_distance:
        description:
            - Assign route administrative distance e.g. 1
        type: int
    route_trace:
        description:
            - TRACEROUTE source IP setting
        type: str
"""

EXAMPLES = """
- name: Enabling routing, multicast
  onyx_static_route:
    routing: True
    multicasting: True
    vrf: vrf2

- name: Assing new static hostname
  onyx_static_route:
    hostname: onyx_sw
    hostname_map: True

- name: Add new route
  onyx_static_route:
    route_type: default
    network_prefix: 1.1.1.1
    netmask: /24
    nexthop: 3.2.2.2

- name: Add multicast route
  onyx_static_route:
    route_type: multicast
    network_prefix: 1.1.1.1
    netmask: /24
    nexthop: 3.2.2.2

- name: Add multicast route in vrf
  onyx_static_route:
    route_type: multicast
    vrf_name: default
    network_prefix: 1.1.1.1
    netmask: /16
    nexthop: 3.2.2.2
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - ip route 10.2.2.2 /24 10.3.3.3
    - ip route 10.2.2.2 /24 10.3.3.3 1
    - ip route vrf vrf-name 1.1.1.1 /24 3.2.2.2 1
    - ip routing
    - ip routing vrf vrf-name
    - ip map-hostname
    - ip host hostname
    - ip mroute 1.1.1.1 /24 2.2.2.2
    - ip mroute 1.1.1.1 /24 2.2.2.2 255
    - ip mroute vrf default 1.1.1.1 /24 2.2.2.2 255
    - ip multicast-routing
    - ip multicast-routing vrf vrf-name
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule, show_cmd
from ansible.module_utils.network.common.utils import is_netmask


class OnyxStaticRouteModule(BaseOnyxModule):
    NETMASK = re.compile(r'\/\d{1,3}')
    ROUTE_RGX = re.compile(r'ip route(\svrf ([a-z]+)\s|\s)([0-9\.]+)(\/\d+|\s\/\d+) ([a-z0-9\.]+)(\s\d+|)')
    MROUTE_RGX = re.compile(r'ip mroute(\svrf ([a-z]+)\s|\s)([0-9\.]+)(\/\d+|\s\/\d+) ([a-z0-9\.]+)(\s\d+|)')
    ROUTING_RGX = re.compile(r'ip routing vrf ([a-z0-9]+)')
    MULTICAST_RGX = re.compile(r'ip multicast-routing vrf ([a-z0-9]+)')
    ROUTETRACE_RGX = re.compile(r'ip traceroute source-interface ([a-z0-9]+)')
    IPHOST_RGX = re.compile(r'ip host (\S+) ([0-9\.]+)')  # ip host spider-144 8.8.8.144
    VRFS_RGX = re.compile(r'vrf definition (\S+).*')
    MAPHOST_RGX = re.compile(r'(no |)ip map-hostname')
    DOMAIN_RGX = re.compile(r'ip domain\-list (\S+)')

    def init_module(self):
        """
        module initialization
        """
        element_spec = dict()

        argument_spec = dict(route_type=dict(choices=['default', 'multicast']),
                             multicasting=dict(type="bool"),
                             vrf_name=dict(type='str'),
                             network_prefix=dict(type='str'),
                             netmask=dict(type='str'),
                             nexthop=dict(type='str'),
                             domain=dict(type='str'),
                             domain_remove=dict(type='bool', default=False),
                             routing=dict(type='bool'),
                             hostname=dict(type='str'),
                             hostip=dict(type='str'),
                             hostname_map=dict(type='bool'),
                             hostname_remove=dict(type='bool', default=False),
                             route_enable=dict(type='bool', default=True),
                             mroute_preference=dict(type='int'),
                             route_distance=dict(type='int'),
                             route_trace=dict(type='str')
                             )

        argument_spec.update(element_spec)
        required_if_rules = [['hostname_remove', True, ('hostname',)],
                             ['domain_remove', True, ('domain',)],
                             ['routing', True, ('vrf_name',)]]
        mutually_exclusive_rules = [['route_distance', 'mroute_preference']]
        required_together_rules = [['route_type', 'network_prefix', 'netmask', 'nexthop'], ['hostname', 'hostip']]

        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=required_if_rules,
            mutually_exclusive=mutually_exclusive_rules,
            required_together=required_together_rules)

    def validate_netmask(self, netmask):
        if netmask is not None:
            match = self.NETMASK.match(netmask)
            if not match and not is_netmask(netmask):
                self._module.fail_json(msg="Invalid network mask")

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        # required if multicasting not None
        if module_params.get('multicasting') is not None:
            if module_params.get('vrf_name') is None:
                self._module.fail_json(msg="Enable/Disable multicasting must have vrf_name attribute")
                return
        for key, value in module_params.items():
            if value is not None:
                self._required_config[key] = value
        self.validate_param_values(self._required_config)

    def _get_routing_config(self):
        routing_config = dict()
        filter_vrf_cmd = "show running-config | include vrf.*definition"
        filter_ip_cmd = "show running-config | include ip"
        vrf_data = show_cmd(self._module, filter_vrf_cmd, json_fmt=True, fail_on_error=False)
        lines = vrf_data.get('Lines')
        if lines:
            routing_config['vrfs'] = lines

        routing_data = show_cmd(self._module, filter_ip_cmd, json_fmt=True, fail_on_error=False)
        lines = routing_data.get('Lines')
        if lines:
            routing_config['routing'] = lines

        return routing_config

    def _set_current_config(self, routes_config):
        if not routes_config:
            return
        current_config = self._current_config
        current_config['hostmap'] = dict()  # to store mapped ip - hostname
        current_config['vrf_list'] = set(['default'])  # avoid any duplication
        vrf_lines = routes_config.get('vrfs', [])
        routes_lines = routes_config.get('routing', [])

        for line in vrf_lines:
            line = line.strip()
            match = self.VRFS_RGX.match(line)
            if match:
                vrf = match.group(1)
                current_config['vrf_list'].add(vrf)

        for line in routes_lines:
            line = line.strip()
            match = self.ROUTE_RGX.match(line)
            if match is not None:
                '''match group(1) will be vrf string or nothing'''
                vrf_name = match.group(2)
                network_prefix = match.group(3)
                netmask = match.group(4)
                destination = match.group(5)
                distance = match.group(6)
                config = {
                    'network_prefix': network_prefix,
                    'netmask': netmask,
                    'nexthop': destination
                }
                if distance != '':
                    config['route_distance'] = distance
                if vrf_name != '':
                    ''' add this route to this vrf '''
                    current_config[vrf_name] = current_config.get(vrf_name, {})
                    current_config[vrf_name].update({network_prefix: config})
                else:
                    current_config[network_prefix] = config
                continue

            match = self.MROUTE_RGX.match(line)
            if match is not None:
                '''match group(1) will be vrf or nothing'''
                vrf_name = match.group(2)
                network_prefix = match.group(3)
                netmask = match.group(4)
                destination = match.group(5)
                mroute_preference = match.group(6)
                cconfig = {
                    'network_prefix': network_prefix,
                    'netmask': netmask,
                    'nexthop': destination,
                    'multicast': True
                }
                if mroute_preference != '':
                    cconfig['mroute_preference'] = mroute_preference

                if vrf_name != '':
                    ''' add this route to this vrf '''
                    current_config[vrf_name] = current_config.get(vrf_name, {})
                    current_config[vrf_name].update({network_prefix: config})
                else:
                    config[network_prefix] = config
                continue

            match = self.ROUTING_RGX.match(line)
            if match is not None:
                vrf = match.group(1)
                current_config['routing'] = current_config.get('routing', []) + [vrf]  # or use defaultdict same thing
                continue

            match = self.MULTICAST_RGX.match(line)
            if match is not None:
                mvrf = match.group(1)
                current_config['multicast_routing'] = current_config.get('multicast_routing', []) + [mvrf]
                continue

            match = self.ROUTETRACE_RGX.match(line)
            if match is not None:
                vrf = match.group(1)
                current_config['routetrace'] = current_config.get('routetrace', []) + [vrf]
                continue

            match = self.IPHOST_RGX.match(line)
            if match is not None:
                hostname = match.group(1)
                hostip = match.group(2)
                current_config['hostmap'][hostip] = current_config['hostmap'].get(hostip, []) + [hostname]
                continue

            match = self.MAPHOST_RGX.match(line)
            if match:
                enabled = match.group(1).strip() != 'no'
                current_config['hostname_map'] = enabled
                continue

            match = self.DOMAIN_RGX.match(line)
            if match:
                domain = match.group(1)
                current_config['domain_list'] = current_config.get('domain_list', []) + [domain]

    def load_current_config(self):
        self._current_config = dict()
        routes_config = self._get_routing_config()
        self._set_current_config(routes_config)

    def _dict_match(self, dict1, dict2):
        '''Check if dict2 keys have values and not equal to dict1'''
        return all([dict1.get(key) == dict2.get(key) for key in dict1 if dict2.get(key) is not None])

    def generate_commands(self):
        current_config, required_config = self._current_config, self._required_config
        print(required_config)
        route = required_config.get('route_type')
        vrf_name = required_config.get('vrf_name')
        route_enable = required_config.get('route_enable')
        vrf_list = current_config.get('vrf_list')

        if vrf_name is not None:
            if vrf_name not in vrf_list:
                self._module.fail_json(msg="vrf {0} does not exist in vrf list {1}".format(vrf_name, vrf_list))

        if route is not None:  # default and multicast route have the same structure
            route_cmd = 'route' if route == 'default' else 'mroute'
            route_distance = required_config.get('route_distance')
            mroute_preference = required_config.get('mroute_preference')
            network_prefix = required_config.get('network_prefix')
            current_route = None
            if vrf_name is not None:
                current_vrf = current_config.get(vrf_name)
                if current_vrf is not None:
                    current_route = current_config[vrf_name].get(network_prefix)
            else:
                current_route = current_config.get(network_prefix)
            required_route = {
                'network_prefix': network_prefix,
                'netmask': required_config.get('netmask'),
                'nexthop': required_config.get('nexthop')
            }

            ''' [route_distance, mroute_preference] one of them will be setted or None '''
            if route_distance is not None:
                required_route['route_distance'] = route_distance
            elif mroute_preference is not None:
                required_route['mroute_preference'] = mroute_preference
            required_str_list = list(map(str, required_route.values()))  # cast to string to able to join them
            if current_route is not None:
                is_no_change = self._dict_match(current_route, required_route)

                if vrf_name is not None:
                    if route_enable is False and is_no_change is True:
                        self._commands.append('no ip {0} vrf {1} {2}'.format(route_cmd, vrf_name, ' '.join(required_str_list)))
                    elif route_enable is True and is_no_change is False:  # just add a new route
                        self._commands.append('ip {0} vrf {1} {2}'.format(route_cmd, vrf_name, ' '.join(required_str_list)))
                else:
                    if route_enable is False and is_no_change is True:
                        self._commands.append('no ip {0} {1}'.format(route_cmd, ' '.join(required_str_list)))
                    elif is_no_change is False:
                        print(required_str_list)
                        self._commands.append('ip {0} {1}'.format(route_cmd, ' '.join(required_str_list)))
            elif route_enable is True:  # new route
                if vrf_name is not None:
                    self._commands.append('ip {0} vrf {1} {2}'.format(route_cmd, vrf_name, ' '.join(required_str_list)))
                else:
                    self._commands.append('ip {0} {1}'.format(route_cmd, ' '.join(required_str_list)))

        mapping_hostname = required_config.get('hostname_map')  # its a command no need to check current config
        if mapping_hostname is not None:
            if mapping_hostname != current_config.get('hostname_map'):
                self._commands.append('{0}ip map-hostname'.format('no ' if not mapping_hostname else ''))

        hostname = required_config.get('hostname')
        if hostname is not None:
            hostip = required_config.get('hostip')
            hostname_remove = required_config.get('hostname_remove')
            current_hostip_list = current_config['hostmap'].get(hostip, [])  # get hostnames for this ip
            if hostname_remove is True:
                if hostname in current_hostip_list:
                    self._commands.append('no ip host {0} {1}'.format(hostname, hostip))
            elif hostname not in current_hostip_list:
                self._commands.append('ip host {0} {1}'.format(hostname, hostip))

        multicasting = required_config.get('multicasting')
        if multicasting is not None and vrf_name is not None:
            vrf_list = current_config.get('multicast_routing')
            if multicasting and vrf_name not in vrf_list:
                self._commands.append('ip multicast-routing vrf {0}'.format(vrf_name))
            elif not multicasting and vrf_name in vrf_list:
                self._commands.append('no ip multicast-routing vrf {0}'.format(vrf_name))

        routing = required_config.get('routing')
        if routing is not None:
            vrf_list = current_config.get('routing')
            if routing and vrf_name not in vrf_list:
                self._commands.append('ip routing vrf {0}'.format(vrf_name))
            elif not routing and vrf_name in vrf_list:
                self._commands.append('no ip routing vrf {0}'.format(vrf_name))

        domain = required_config.get('domain')
        if domain is not None:
            is_remove_action = required_config.get('domain_remove')
            is_listed_domain = domain in current_config.get('domain_list', [])
            if is_remove_action is True and is_listed_domain:
                self._commands.append('no ip domain-list {0}'.format(domain))
            elif is_remove_action is False and not is_listed_domain:
                self._commands.append('ip domain-list {0}'.format(domain))


def main():
    """ main entry point for module execution
    """
    OnyxStaticRouteModule.main()


if __name__ == '__main__':
    main()
