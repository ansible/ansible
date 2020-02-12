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
module: awplus_lag_interfaces
author: Cheng Yi Kok (@cyk19)
short_description: Manage Link Aggregation on AlliedWare Plus devices.
description: This module manages properties of Link Aggregation Group on AlliedWare Plus devices.
version_added: "2.10"
options:
  config:
    description: A list of link aggregation group configurations.
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - ID of Ethernet Channel of interfaces.
          - Refer to vendor documentation for valid port values.
        type: str
        required: True
      members:
        description:
          - Interface options for the link aggregation group.
        type: list
        suboptions:
          member:
            description:
              - Interface member of the link aggregation group.
            type: str
          mode:
            description:
              - Etherchannel Mode of the interface for link aggregation.
            type: str
            choices:
              - 'auto'
              - 'on'
              - 'desirable'
              - 'active'
              - 'passive'
  state:
    description:
      - The state of the configuratiion after module completion
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
# interface po10
#  switchport
#  switchport mode access
# !
    - name: Merge provided configuration with device configuration
      awplus_lag_interfaces:
        config:
          - name: 10
            members:
              - member: port1.0.4
                mode: active
              - member: port1.0.3
                mode: active
        state: merged
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
#  switchport access vlan 3
#  channel-group 2 mode active
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
#  channel-group 10 mode active
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  channel-group 10 mode active
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
# interface po10
#  switchport
#  switchport mode access
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
#  channel-group 10 mode active
# !
    - name: Override device configuration of all interfaces with provided configuration
      awplus_lag_interfaces:
        config:
          - name: 10
            members:
              - member: port1.0.4
                mode: passive
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
#  channel-group 10 mode passive
# !

# Using replaced
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
#  switchport access vlan 3
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
# !
    - name: Replaces device configuration of listed interfaces with provided configuration
      awplus_lag_interfaces:
        config:
          - name: 40
            members:
            - member: port1.0.3
              mode: active
        state: replaced
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
#  switchport access vlan 3
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
#  channel-group 40 mode active
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
#  switchport access vlan 3
#  channel-group 2 mode active
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
#  channel-group 10 mode active
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  channel-group 10 mode active
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
# interface po10
#  switchport
#  switchport mode access
# !
  - name: Delete LAG attributes of given interfaces
    awplus_lag_interfaces:
      config:
        - name: 10
      state: deleted
# After state:
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


# Using Deleted without any config passed
#"(NOTE: This will delete all of configured LLDP module attributes)"
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
#  switchport access vlan 3
# !
# interface port1.0.3
#  speed 1000
#  duplex full
#  switchport
#  switchport mode access
#  channel-group 40 mode active
# !
# interface port1.0.4
#  switchport
#  switchport mode access
#  channel-group 10 mode passive
# !
    - name: Delete all configured LAG attributes for interfaces
      awplus_lag_interfaces:
        state: deleted
# After state:
# -------------
#
# # aw1#show running-config interface
# # interface port1.0.1
# #  switchport
# #  switchport mode access
# # !
# # interface port1.0.2
# #  description test interface
# #  duplex full
# #  shutdown
# #  switchport
# #  switchport mode access
# #  switchport access vlan 3
# # !
# # interface port1.0.3
# #  speed 1000
# #  duplex full
# #  switchport
# #  switchport mode access
# # !
# # interface port1.0.4
# #  switchport
# #  switchport mode access
# # !

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
from ansible.module_utils.network.awplus.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs
from ansible.module_utils.network.awplus.config.lag_interfaces.lag_interfaces import Lag_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lag_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Lag_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
