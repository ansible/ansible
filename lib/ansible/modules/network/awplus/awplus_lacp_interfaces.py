#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.argspec.lacp_interfaces.lacp_interfaces import Lacp_interfacesArgs
from ansible.module_utils.network.awplus.config.lacp_interfaces.lacp_interfaces import Lacp_interfaces

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': '<support_group>'
}

DOCUMENTATION = """
---
module: awplus_lacp_interfaces
author: Cheng Yi Kok (@cyk19)
short_description: Manage Link Aggregation Control Protocol (LACP) on
                    AlliedWare Plus devices interface.
description: This module provides declarative management of LACP on AlliedWare
              Plus network devices lacp_interfaces.
version_added: "2.10"
options:
  config:
    description: A dictionary of LACP lacp_interfaces option
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name of the Interface for configuring LACP.
        type: str
        required: True
      port_priority:
        description:
          - LACP priority on this interface.
          - Refer to vendor documentation for valid port values.
        type: int
      timeout:
        description:
          - Set the short or long timeout on a port.
          - Ports will time out of the aggregation if three consecutive updates are lost
        type: str
        default: long
  state:
    description:
      - The state of the configuration after module completion
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
    default: merged
"""

EXAMPLES = """
# Using merged
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
#  switchport access vlan 3
#  channel-group 2 mode active
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
# interface po2
#  switchport
#  switchport mode access
#  switchport access vlan 3
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
  - name: Merge provided configuration with device configuration
    awplus_lacp_interfaces:
      config:
        - name: port1.0.2
          port_priority: 2
      state: merged
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 2
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
# interface po2
#  switchport
#  switchport mode access
#  switchport access vlan 3
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 2
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
# interface po2
#  switchport
#  switchport mode access
#  switchport access vlan 3
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
  - name: Replace provided configuration with device configuration
    awplus_lacp_interfaces:
      config:
        - name: port1.0.2
          port_priority: 3
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 3

# Using overridden
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 3
  - name: Override provided configuration with device configuration
    awplus_lacp_interfaces:
      config:
        - name: port1.0.2
          port_priority: 4
        state: overridden
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 4
# !

# Using Deleted
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 4
# !
  - name: Delete LACP attributes of given interfaces
    awplus_lacp_interfaces:
      config:
          - name: port1.0.2
      state: deleted
# After state:
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
#  switchport access vlan 3
#  channel-group 2 mode active
# !

# Using Deleted without any config passed
# "(NOTE: This will delete all of configured LLDP module attributes)"
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
#  switchport access vlan 3
#  channel-group 2 mode active
#  lacp port-priority 4
# !
- name: Delete LACP attributes of all interfaces
  awplus_lacp_interfaces:
    state: deleted
# After state:
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
#  switchport access vlan 3
#  channel-group 2 mode active
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


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lacp_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Lacp_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
