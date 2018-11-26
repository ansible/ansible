#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: ios_bgp
version_added: "2.8"
author: "Nilashish Chakraborty (@nilashishc)"
short_description: Configure global BGP protocol settings on Cisco IOS
description:
  - This module provides configuration management of global BGP parameters
    on devices running Cisco IOS
notes:
  - Tested against Cisco IOS Version 15.6(3)M2
options:
  bgp_as:
    description:
      - Specifies the BGP Autonomous System number to configure on the device
    type: int
    required: true
  router_id:
    description:
      - Configures the BGP routing process router-id value
    default: null
  log_neighbor_changes:
    description:
      - Enable/Disable logging neighbor up/down and reset reason
    type: bool
  neighbors:
    description:
      - Specifies BGP neighbor related configurations
    suboptions:
      neighbor:
        description:
          - Neighbor router address
        required: True
      remote_as:
        description:
          - Remote AS of the BGP neighbor to configure
        type: int
        required: True
      route_reflector_client:
        description:
          - Specify a neighbor as a route reflector client
        type: bool
      update_source:
        description:
          - Source of the routing updates
      password:
        description:
          - Password to authenticate BGP peer connection
      enabled:
        description:
          - Administratively shutdown or enable a neighbor
        type: bool
      description:
        description:
          - Neighbor specific description
      ebgp_multihop:
        description:
          - Specifies the maximum hop count for EBGP neighbors not on directly connected networks
        type: int
      peer_group:
        description:
          - Name of peer-group of which the neighbor is a member
      timers:
        description:
          - Specifies BGP neighbor timer related configurations
        suboptions:
          keepalive:
            description:
              - Frequency (in seconds) with which the Cisco IOS software sends keepalive messages to its peer.
              - The range is from 0 to 65535.
            type: int
            required: True
          holdtime:
            description:
              - Interval (in seconds) after not receiving a keepalive message that the software declares a peer dead.
              - The range is from 0 to 65535.
            type: int
            required: True
          min_neighbor_holdtime:
            description:
              - Interval (in seconds) specifying the minimum acceptable hold-time from a BGP neighbor.
              - The minimum acceptable hold-time must be less than, or equal to, the interval specified in the holdtime argument.
              - The range is from 0 to 65535.
            type: int
      state:
        description:
          - Specifies the state of the BGP neighbor
        default: present
        choices:
          - present
          - absent
  networks:
    description:
      - Specify networks to announce via BGP
    suboptions:
      network:
        description:
          - Network ID to announce via BGP
        required: True
      mask:
        description:
          - Subnet Mask for the Network to announce
      route_map:
        description:
          - Route-map to modify the attributes
      state:
        description:
          - Specifies the state of network
        default: present
        choices:
          - present
          - absent
  address_families:
    description:
      - Specifies BGP address family related configurations
    suboptions:
      name:
        description:
          - Type of address family to configure
        choices:
          - ipv4
          - ipv6
        required: True
      cast:
        description:
          - Specifies the type of cast for the address family
        choices:
          - flowspec
          - unicast
          - multicast
          - labeled-unicast
        default: unicast
      redistribute:
        description:
          - Specifies the redistribute information from another routing protocol
        suboptions:
          protocol:
            description:
              - Specifies the protocol for configuring redistribute information
            required: True
          id:
            description:
              - Identifier for the routing protocol for configuring redistribute information
              - Not valid for protocol - RIP
          metric:
            description:
              - Specifies the metric for redistributed routes
          route_map:
            description:
              - Specifies the route map reference
          state:
            description:
              - Specifies the state of redistribution
            default: present
            choices:
              - present
              - absent
      networks:
        description:
          - Specify networks to announce via BGP
        suboptions:
          network:
            description:
              - Network ID to announce via BGP
            required: True
          mask:
            description:
              - Subnet Mask for the Network to announce
          route_map:
            description:
              - Route-map to modify the attributes
          state:
            description:
              - Specifies the state of network
            default: present
            choices:
              - present
              - absent
      auto_summary:
        description:
          - Enable automatic network number summarization
        type: bool
      synchronization:
        description:
          - Enable IGP synchronization
        type: bool
      state:
        description:
          - Specifies the state of address family
        default: present
        choices:
          - present
          - absent
  state:
    description:
      - Specifies the state of the BGP process configured on the device
    default: present
    choices:
      - present
      - absent
      - replace
extends_documentation_fragment: ios
"""

EXAMPLES = """
- name: configure global bgp as 65000
  ios_bgp:
    bgp_as: 65000
    router_id: 1.1.1.1
    log_neighbor_changes: True
    neighbors:
      - neighbor: 182.168.10.1
        remote_as: 500
      - neighbor: 192.168.20.1
        remote_as: 500
    networks:
      - network: 10.0.0.0/8
      - network: 11.0.0.0/8
    state: present

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
    - router bgp 500
    - neighbor 182.168.10.1 remote-as 500
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ios.ios import get_config, load_config
from ansible.module_utils.network.ios.config.bgp import get_bgp_as
from ansible.module_utils.network.ios.config.bgp.process import BgpProcess
from ansible.module_utils.network.ios.ios import ios_argument_spec


def main():
    """ main entry point for module execution
    """
    argument_spec = BgpProcess.argument_spec
    argument_spec.update(ios_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    config = get_config(module, flags=['| section bgp'])

    result = {'changed': False}
    commands = list()

    bgp_as = get_bgp_as(config)

    if all((module.params['bgp_as'] is None, bgp_as is None)):
        module.fail_json(msg='missing required argument: bgp_as')
    elif module.params['bgp_as'] is None and bgp_as:
        module.params['bgp_as'] = bgp_as

    process = BgpProcess(**module.params)

    resp = process.render(config)
    if resp:
        commands.extend(resp)
    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
