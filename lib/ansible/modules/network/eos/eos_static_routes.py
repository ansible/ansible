#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for eos_static_routes
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network'
}

DOCUMENTATION = """
---
module: eos_static_routes
version_added: 2.10
short_description: Configures and manages attributes of static routes on Arista EOS platforms.
description: This module configures and manages the attributes of static routes on Arista EOS platforms.
author: Gomathi Selvi Srinivasan (@GomathiselviS)
notes:
options:
  config:
    description:
      - A list of configurations for static routes.
    type: list
    elements: dict
    suboptions:
      vrf:
        description:
          - The VRF to which the static route(s) belong.
        type: str
      address_families:
        description: A dictionary specifying the address family to which the static route(s) belong.
        type: list
        elements: dict
        suboptions:
          afi:
            description:
              - Specifies the top level address family indicator.
            type: str
            choices: ['ipv4', 'ipv6']
            required: True
          routes:
            description: A dictionary that specifies the static route configurations.
            elements: dict
            type: list
            suboptions:
              dest:
                description: 
                  - Destination IPv4 subnet (CIDR or address-mask notation).
                  - The address format is <v4/v6 address>/<mask> or <v4/v6 address> <mask>.
                  - The mask is number in range 0-32 for IPv4 and in range 0-128 for IPv6.
                type: str
                required: True
              next_hops: 
                description: 
                  - Details of route to be taken.
                type: list
                elements: dict
                suboptions:
                  forward_router_address:
                    description:
                      - Forwarding router's address on destination interface.
                    type: str
                  interface:
                    description:
                      - Outgoing interface to take. For anything except 'null0', then next hop IP address should also be configured.
                      - IP address of the next hop router or
                      - null0 Null0 interface or
                      - ethernet e_num Ethernet interface or
                      - loopback l_num Loopback interface or
                      - management m_num Management interface or
                      - port-channel p_num
                      - vlan v_num
                      - vxlan vx_num
                      - Nexthop-Group  Specify nexthop group name
                      - Tunnel  Tunnel interface
                      - vtep  Configure VXLAN Tunnel End Points
                    type: str
                  nexthop_grp:
                    description:
                        - Nexthop group
                    type: str
                  admin_distance:
                    description: 
                      - Preference or administrative distance of route (range 1-255).
                    type: int
                  description:
                    description:
                      - Name of the static route.
                    type: str
                  tag:
                    description:
                      - Route tag value (ranges from 0 to 4294967295).
                    type: int
                  track:
                    description:
                      - Track value (range 1 - 512). Track must already be configured on the device before adding the route.
                    type: str
                  mpls_label:
                    description:
                      - MPLS label
                    type: int
                  vrf:
                    description:
                      - VRF of the destination.
                    type: str
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
      ['deleted', 'merged', 'overridden', 'replaced', 'gathered', 'rendered']
    default:
      merged
"""
EXAMPLES = """
# Using deleted

Before State
-------------
veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 100
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 5001::/64 Ethernet1 50
veos(config)#

- name: Delete static route configuration
  eos_static_routes:
    state: deleted

After State
-----------

veos(config)#show running-config | grep "route"
veos(config)#


# Using merged

Before State
-------------
veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 100
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 5001::/64 Ethernet1 50
veos(config)#

- name: Merge new static route configuration
  eos_static_routes:
    config:
      - vrf: testvrf
        address_families:
          - afi: ipv6
            routes:
              - dest: 2211::0/64
                next_hop: 
                  - forward_router_address: 100:1::2
                    interface: "Ethernet1"                
    state: merged

After State
-----------

veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 100
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 2211::/64 Ethernet1 100:1::2
ipv6 route 5001::/64 Ethernet1 50
veos(config)#


# Using overridden

Before State
-------------
veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 100
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 5001::/64 Ethernet1 50
veos(config)#

- name: Overridden static route configuration
  eos_static_routes:
    config:
      - vrf: testvrf
        address_families:
          - afi: ipv4
            routes:
              - dest: 150.10.1.0/24
                next_hop:
                  - forward_router_address: 10.1.1.2
                    interface: "Ethernet1"
    state: replaced

After State
-----------

veos(config)#show running-config | grep "route"
ip route 150.10.1.0/24 Ethernet1 10.1.1.2
veos(config)#


# Using replaced

Before State
-------------
veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 100
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 5001::/64 Ethernet1 50
veos(config)#

- name: Replace static route configuration
  eos_static_routes:
    config:
      - vrf: testvrf
        address_families:
          - afi: ipv4
            routes:
              - dest: 165.10.1.0/24
                next_hop:
                  - forward_router_address: 10.1.1.2
                    interface: "Ethernet1"
    state: replaced

After State
-----------

veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 10.1.1.2
ip route 172.17.252.0/24 Nexthop-Group testgroup
ip route vrf testvrf 130.1.122.0/24 Ethernet1 tag 50
ipv6 route 2211::/64 Ethernet1 100:1::2
ipv6 route 5001::/64 Ethernet1 50
veos(config)#


Before State
-------------
veos(config)#show running-config | grep "route"
ip route 165.10.1.0/24 Ethernet1 10.1.1.2 100
ipv6 route 5001::/64 Ethernet1
veos(config)#


- name: Gather the exisitng condiguration
  eos_static_routes:
    state: gathered


returns :
  eos_static_routes:
    config:
      - address_families:
          - afi: ipv4
            routes:
              - dest: 165.10.1.0/24
                next_hop:
                  - forward_router_address: 10.1.1.2
                    interface: "Ethernet1"
		    admin_distance: 100
         - afi: ipv6
            routes:
              - dest: 5001::/64
                next_hop:
                  - interface: "Ethernet1"	


# Using rendered

i  eos_static_routes:
    config:
      - address_families:
          - afi: ipv4
            routes:
              - dest: 165.10.1.0/24
                next_hop:
                  - forward_router_address: 10.1.1.2
                    interface: "Ethernet1"
                    admin_distance: 100
         - afi: ipv6
            routes:
              - dest: 5001::/64
                next_hop:
                  - interface: "Ethernet1"



returns:

ip route 165.10.1.0/24 Ethernet1 10.1.1.2 100
ipv6 route 5001::/64 Ethernet1


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.argspec.static_routes.static_routes import Static_routesArgs
from ansible.module_utils.network.eos.config.static_routes.static_routes import Static_routes


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Static_routesArgs.argument_spec,
                           supports_check_mode=True)

    result = Static_routes(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
