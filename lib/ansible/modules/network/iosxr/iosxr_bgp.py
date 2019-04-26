#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_bgp
version_added: "2.8"
author: "Nilashish Chakraborty (@nilashishc)"
short_description: Configure global BGP protocol settings on Cisco IOS-XR
description:
  - This module provides configuration management of global BGP parameters
    on devices running Cisco IOS-XR
notes:
  - Tested against Cisco IOS XR Software Version 6.1.3
options:
  config:
    description:
      - Specifies the BGP related configuration.
    suboptions:
      bgp_as:
        description:
          - Specifies the BGP Autonomous System (AS) number to configure on the device.
        type: int
        required: true
      router_id:
        description:
          - Configures the BGP routing process router-id value.
        default: null
      log_neighbor_changes:
        description:
          - Enable/disable logging neighbor up/down and reset reason.
        type: bool
      neighbors:
        description:
          - Specifies BGP neighbor related configurations.
        suboptions:
          neighbor:
            description:
              - Neighbor router address.
            required: True
          remote_as:
            description:
              - Remote AS of the BGP neighbor to configure.
            type: int
            required: True
          update_source:
            description:
              - Source of the routing updates.
          password:
            description:
              - Password to authenticate the BGP peer connection.
          enabled:
            description:
              - Administratively shutdown or enable a neighbor.
            type: bool
          description:
            description:
              - Neighbor specific description.
          advertisement_interval:
            description:
              - Specifies the minimum interval (in seconds) between sending BGP routing updates.
              - The range is from 0 to 600.
            type: int
          tcp_mss:
            description:
              - Specifies the TCP initial maximum segment size to use.
              - The range is from 68 to 10000.
            type: int
          ebgp_multihop:
            description:
              - Specifies the maximum hop count for EBGP neighbors not on directly connected networks.
              - The range is from 0 to 255.
            type: int
          timers:
            description:
              - Specifies BGP neighbor timer related configurations.
            suboptions:
              keepalive:
                description:
                  - Frequency with which the Cisco IOS-XR software sends keepalive messages to its peer.
                  - The range is from 0 to 65535.
                type: int
                required: True
              holdtime:
                description:
                  - Interval after not receiving a keepalive message that the software declares a peer dead.
                  - The range is from 3 to 65535.
                type: int
                required: True
              min_neighbor_holdtime:
                description:
                  - Interval specifying the minimum acceptable hold-time from a BGP neighbor.
                  - The minimum acceptable hold-time must be less than, or equal to, the interval specified in the holdtime argument.
                  - The range is from 3 to 65535.
                type: int
      address_family:
        description:
          - Specifies BGP address family related configurations.
        suboptions:
          afi:
            description:
              - Type of address family to configure.
            choices:
              - ipv4
              - ipv6
            required: True
          safi:
            description:
              - Specifies the type of cast for the address family.
            choices:
              - flowspec
              - unicast
              - multicast
              - labeled-unicast
            default: unicast
          redistribute:
            description:
              - Specifies the redistribute information from another routing protocol.
            suboptions:
              protocol:
                description:
                  - Specifies the protocol for configuring redistribute information.
                choices: ['ospf', 'ospfv3', 'eigrp', 'isis', 'static', 'connected', 'lisp', 'mobile', 'rip', 'subscriber']
                required: True
              id:
                description:
                  - Identifier for the routing protocol for configuring redistribute information.
                  - Valid for protocols 'ospf', 'eigrp', 'isis' and 'ospfv3'.
              metric:
                description:
                  - Specifies the metric for redistributed routes.
              route_map:
                description:
                  - Specifies the route map reference.
          networks:
            description:
              - Specify networks to announce via BGP.
              - For operation replace, this option is mutually exclusive with root level networks option.
            suboptions:
              network:
                description:
                  - Network ID to announce via BGP.
                required: True
              masklen:
                description:
                  - Subnet mask length for the network to announce(e.g, 8, 16, 24, etc.).
              route_map:
                description:
                  - Route map to modify the attributes.
  operation:
    description:
      - Specifies the operation to be performed on the BGP process configured on the device.
      - In case of merge, the input configuration will be merged with the existing BGP configuration on the device.
      - In case of replace, if there is a diff between the existing configuration and the input configuration, the
        existing configuration will be replaced by the input configuration for every option that has the diff.
      - In case of override, all the existing BGP configuration will be removed from the device and replaced with
        the input configuration.
      - In case of delete the existing BGP configuration will be removed from the device.
    default: merge
    choices: ['merge', 'replace', 'override', 'delete']
"""

EXAMPLES = """
- name: configure global bgp as 65000
  iosxr_bgp:
    bgp_as: 65000
    router_id: 1.1.1.1
    neighbors:
      - neighbor: 182.168.10.1
        remote_as: 500
        description: PEER_1
      - neighbor: 192.168.20.1
        remote_as: 500
        update_source: GigabitEthernet 0/0/0/0
    address_family:
      - name: ipv4
        cast: unicast
        networks:
          - network: 192.168.2.0/23
          - network: 10.0.0.0/8
        redistribute:
          - protocol: ospf
            id: 400
            metric: 110

- name: remove bgp as 65000 from config
  ios_bgp:
    bgp_as: 65000
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - router bgp 65000
    - bgp router-id 1.1.1.1
    - neighbor 182.168.10.1 remote-as 500
    - neighbor 182.168.10.1 description PEER_1
    - neighbor 192.168.20.1 remote-as 500
    - neighbor 192.168.20.1 update-source GigabitEthernet0/0/0/0
    - address-family ipv4 unicast
    - redistribute ospf 400 metric 110
    - network 192.168.2.0/23
    - network 10.0.0.0/8
    - exit
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.network.iosxr.providers.module import NetworkModule
from ansible.module_utils.network.iosxr.providers.cli.config.bgp.process import REDISTRIBUTE_PROTOCOLS


def main():
    """ main entry point for module execution
    """
    network_spec = {
        'prefix': dict(required=True),
        'masklen': dict(type='int', required=True),
        'route_map': dict(),
    }

    redistribute_spec = {
        'protocol': dict(choices=REDISTRIBUTE_PROTOCOLS, required=True),
        'id': dict(),
        'metric': dict(type='int'),
        'route_map': dict(),
    }

    timer_spec = {
        'keepalive': dict(type='int'),
        'holdtime': dict(type='int'),
        'min_neighbor_holdtime': dict(type='int'),
    }

    neighbor_spec = {
        'neighbor': dict(required=True),
        'remote_as': dict(type='int', required=True),
        'update_source': dict(),
        'password': dict(no_log=True),
        'enabled': dict(type='bool'),
        'description': dict(),
        'advertisement_interval': dict(type='int'),
        'ebgp_multihop': dict(type='int'),
        'tcp_mss': dict(type='int'),
        'timers': dict(type='dict', options=timer_spec),
    }

    address_family_spec = {
        'afi': dict(choices=['ipv4', 'ipv6'], required=True),
        'safi': dict(choices=['flowspec', 'labeled-unicast', 'multicast', 'unicast'], default='unicast'),
        'networks': dict(type='list', elements='dict', options=network_spec),
        'redistribute': dict(type='list', elements='dict', options=redistribute_spec),
    }

    config_spec = {
        'bgp_as': dict(type='int', required=True),
        'router_id': dict(),
        'log_neighbor_changes': dict(type='bool'),
        'neighbors': dict(type='list', elements='dict', options=neighbor_spec),
        'address_family': dict(type='list', elements='dict', options=address_family_spec),
    }

    argument_spec = {
        'config': dict(type='dict', options=config_spec),
        'operation': dict(default='merge', choices=['merge', 'replace', 'override', 'delete'])
    }

    module = NetworkModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    try:
        result = module.edit_config(config_filter='router bgp')
    except Exception as exc:
        module.fail_json(msg=to_text(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
