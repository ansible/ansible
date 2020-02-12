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
module: awplus_l2_interfaces
author: Cheng Yi Kok (@cyk19)
short_description: Manage Layer-2 interface on AlliedWare Plus devices
description: This module provides declarative management of Layer-2 interface on AW+ devices
version_added: "2.10"
options:
  config:
    description: A dictionary of Layer-2 interface options
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of the interface
        type: str
        required: True
      access:
        description:
        - Switchport mode access command to configure the interfaces as a layer 2 access
        type: dict
        suboptions:
          vlan:
            description:
              - Configure given VLAN in access port. It's used as the access VLAN ID
            type: int
      trunk:
        description:
        - Switchport mode trunk command to configure the interface as a Layer 2 trunk.
        type: dict
        suboptions:
          allowed_vlans:
            description:
              - List of allowed VLANs in a given trunk port. These are the only VLANs that will be
                configured on the trunk.
            type: list
          native_vlan:
            description:
              - Native VLAN to be configured in trunk port. It's used as the trunk native VLAN ID.
            type: int
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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan add 21-25,40
#  switchport trunk native vlan 20
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !

- name: Merge provided configuration with device configuration
  awplus_l2_interfaces:
    config:
      - name: port1.0.4
        access:
          vlan: 10
      - name: port1.0.3
        trunk:
          allowed_vlans: 10-20,40
          native_vlan: 15
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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan add 10-14,16-25,40
#  switchport trunk native vlan 15
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  switchport access vlan 10
# !


# Using replaced

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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk native vlan none
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !

- name: Merge provided configuration with device
  awplus_l2_interfaces:
    config:
      - name: port1.0.3
        trunk:
          allowed_vlans: 20-25,40
          native_vlan: 20
    state: replaced

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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan add 21-25,40
#  switchport trunk native vlan 20
# !
# interface port1.0.4
#  switchport
#  switchport mode access
# !


# Using overridden

# Before state:
# -------------
#
# aw1 show running-config interface
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

  - name: Override device configuration of all l2 interfaces with provided configuration
    awplus_l2_interfaces:
      config:
        - name: port1.0.2
          access:
            vlan: 3
      state: overridden

# After state:
# -------------
#
# aw1 show running-config interface
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


# Using Deleted

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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan add 10-14,16-25,40
#  switchport trunk native vlan 15
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  switchport access vlan 10
# !

    - name: Delete AlliedWare Plus L2 interfaces as in given arguments
      awplus_l2_interfaces:
        config:
          - name: port1.0.3
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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan none
#  switchport trunk native vlan 1
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  switchport access vlan 10
# !


# Using Deleted without any config passed
#"(NOTE: This will delete all of configured resource module attributes from each configured interface)"

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
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode trunk
#  switchport trunk allowed vlan none
#  switchport trunk native vlan 1
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  switchport access vlan 10
# !

- name: Delete all L2 interfaces as in given arguments
  awplus_l2_interfaces:
    state: deleted

# After state:
# -------------
#
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
#  switchport mode trunk
#  switchport trunk allowed vlan none
#  switchport trunk native vlan 1
# !
# interface port1.0.4
#  switchport
#  switchport mode access
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
from ansible.module_utils.network.awplus.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.network.awplus.config.l2_interfaces.l2_interfaces import L2_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=L2_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = L2_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
