#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_l3_interfaces
author: Cheng Yi Kok (@cyk19)
short_description: Manage Layer-3 interface on AlliedWare Plus devices.
description:
- This module provides declarative management of Layer-3 interface on AlliedWare Plus devices
version_added: "2.10"
options:
  config:
    description: A dictionary of Layer-3 interface options
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of the interface
        type: str
        required: True
      ipv4:
        description:
          - IPv4 address to be set for Layer-3 interface mentioned in
            I(name) option. The address format is <ipv4 address>/<mask>,
            the mask is number in range 0-32 eg. 192.168.0.1/24
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - Configures the IPv4 address for Interface
            type: str
          secondary:
            description:
              - Configures the IP address as a secondary address.
            type: bool
          dhcp_client:
            description:
              - Configures and specifies client-id to use over DHCP ip.
                Note, this option shall work only when dhcp is configures as IP.
              - GigabitEthernet interface number
            type: int
          dhcp_hostname:
            description:
              - Configures and specifies value for hostname option over DHCP ip.
                Note, this option shall work only when dhcp is configured as IP.
            type: str
      ipv6:
        description:
          - IPv6 address to be set for the Layer-3 interface mentioned in
            I(name) option.
          - The address format is <ipv6 address>/<mask>, the mask is number
            in range 0-128 eg. fd5f:12c9:2201:1::1/64
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - Configures the IPv6 address for interface
            type: str
  state:
    choices:
      - merged
      - replaced
      - overridden
      - deleted
    default: merged
    description:
      - The state of the configuration after module completion
    type: str
"""

EXAMPLES = """
# Using merged
#
# Before state:
# -------------
#
# aw1#sh running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ipv6 enable
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
- name: Override device configuration of all l3 interfaces with provided configuration
  awplus_l3_interfaces:
    config:
      - name: vlan1
        ipv4:
          - address: 192.168.0.2/24
            secondary: True
    state: merged
# After state:
# ------------
#
# aw1#sh running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 enable
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !

# Using replaced
#
# Before state:
# -------------
#
# aw1(config-if)#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 enable
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ip address 192.168.4.4/24
# !
  - name: Replaces device config of listed interfaces with provided config
    awplus_l3_interfaces:
      config:
        - name: vlan2
          ipv4:
            - address: dhcp
              dhcp_client: 2
              dhcp_hostname: test.com
      state: replaced

# After state:
# ------------
#
# aw1(config-if)#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 enable
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ip address 192.168.4.4/24
# !
# aw1(config-if)#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 enable
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ip address dhcp client-id vlan2 hostname test.com
# !

# Using overridden
#
# Before state:
# -------------
#
# aw1#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ipv6 enable
# !
- name: Override device configuration of all interfaces with provided configuration
  awplus_l3_interfaces:
    config:
      - name: vlan2
        ipv6:
          - address: dhcp
      - name: vlan1
        ipv4:
          - address: 192.168.5.2/24
    state: overridden
# After state:
# ------------
#
# aw1#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ipv6 enable
#  ipv6 address dhcp
# !

# Using Deleted
#
# Before state:
# -------------
#
# aw1#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ipv6 address dhcp
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan2
#  ipv6 enable
#  ipv6 address dhcp
# !
- name: Delete attributes of given interface
  awplus_l3_interfaces:
    config:
      - name: vlan2
    state: deleted
# After state:
# -------------
#
# aw1(config)#show running-config interface
# interface port1.0.1
#  switchport
#  switchport mode access
# !
# interface port1.0.2
#  description test interface
#  duplex full
#  shutdown
#  switchport
#  switchport mode access
#  switchport access vlan 2
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !
# interface eth1
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !
# interface vlan1
#  description Merged by Ansible Network
#  ip address 192.168.5.2/24
#  ip address 192.168.0.2/24 secondary
#  ip dhcp-client vendor-identifying-class
#  ip dhcp-client request vendor-identifying-specific
#  ip helper-address 172.26.1.10
#  ip helper-address 172.26.3.8
# !

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
from ansible.module_utils.network.awplus.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.network.awplus.config.l3_interfaces.l3_interfaces import L3_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=L3_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = L3_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
