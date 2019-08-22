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
The module file for ios_lldp_interfaces
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
module: ios_lldp_interfaces
version_added: 2.9
short_description: Manage link layer discovery protocol (LLDP) attributes of interfaces on Cisco IOS devices.
description: This module manages link layer discovery protocol (LLDP) attributes of interfaces on Cisco IOS devices.
author: Sumit Jaiswal (@justjais)
notes:
  - Tested against Cisco IOSv Version 15.2 on VIRL
  - This module works with connection C(network_cli),
    See L(IOS Platform Options,../network/user_guide/platform_ios.html).
options:
  config:
    description: A dictionary of LLDP options
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of the interface excluding any logical unit number, i.e. GigabitEthernet0/1.
        type: str
        required: True
      receive:
        description:
          - Enable LLDP reception on interface.
        type: bool
      transmit:
        description:
          - Enable LLDP transmission on interface.
        type: bool
      med_tlv_select:
        description:
          - Selection of LLDP MED TLVs to send
          - NOTE, if med-tlv-select is configured idempotency won't be maintained
            as Cisco device doesn't record configured med-tlv-select options. As
            such, Ansible cannot verify if the respective med-tlv-select options is
            already configured or not from the device side. If you try to apply
            med-tlv-select option in every play run, Ansible will show changed as
            True.
        type: dict
        suboptions:
          inventory_management:
            description:
              - LLDP MED Inventory Management TLV
            type: bool
      tlv_select:
        description:
          - Selection of LLDP type-length-value i.e. TLVs to send
          - NOTE, if tlv-select is configured idempotency won't be maintained
            as Cisco device doesn't record configured tlv-select options. As
            such, Ansible cannot verify if the respective tlv-select options is
            already configured or not from the device side. If you try to apply
            tlv-select option in every play run, Ansible will show changed as True.
        type: dict
        suboptions:
          power_management:
            description:
              - IEEE 802.3 DTE Power via MDI TLV
            type: bool
  state:
    description:
    - The state the configuration should be left in
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
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

- name: Merge provided configuration with device configuration
  ios_lldp_interfaces:
    config:
      - name: GigabitEthernet0/1
        receive: True
        transmit: True
      - name: GigabitEthernet0/2
        receive: True
      - name: GigabitEthernet0/3
        transmit: True
    state: merged

# After state:
# ------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

# Using overridden
#
# Before state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

- name: Override device configuration of all lldp_interfaces with provided configuration
  ios_lldp_interfaces:
    config:
      - name: GigabitEthernet0/2
        receive: True
        transmit: True
    state: overridden

# After state:
# ------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME

# Using replaced
#
# Before state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

- name: Replaces device configuration of listed lldp_interfaces with provided configuration
  ios_lldp_interfaces:
    config:
      - name: GigabitEthernet0/2
        receive: True
        transmit: True
      - name: GigabitEthernet0/3
        receive: True
    state: replaced

# After state:
# ------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: disabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

# Using Deleted
#
# Before state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

- name: "Delete LLDP attributes of given interfaces (Note: This won't delete the interface itself)"
  ios_lldp_interfaces:
    config:
      - name: GigabitEthernet0/1
    state: deleted

# After state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

# Using Deleted without any config passed
# "(NOTE: This will delete all of configured LLDP module attributes)"
#
# Before state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: enabled
#    Rx: enabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

- name: "Delete LLDP attributes for all configured interfaces (Note: This won't delete the interface itself)"
  ios_lldp_interfaces:
    state: deleted

# After state:
# -------------
#
# vios#sh lldp interface
# GigabitEthernet0/0:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/1:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#
# GigabitEthernet0/2:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: INIT
#
# GigabitEthernet0/3:
#    Tx: disabled
#    Rx: disabled
#    Tx state: IDLE
#    Rx state: WAIT FOR FRAME
#

"""

RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['interface GigabitEthernet 0/1', 'lldp transmit', 'lldp receive']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ios.argspec.lldp_interfaces.lldp_interfaces import Lldp_InterfacesArgs
from ansible.module_utils.network.ios.config.lldp_interfaces.lldp_interfaces import Lldp_Interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lldp_InterfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Lldp_Interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
