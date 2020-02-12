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
module: awplus_lldp_interfaces
version_added: "2.10"
short_description: Manage link layer discovery protocol (LLDP) attributes of interfaces on AlliedWare Plus devices.
description: This module manages link layer discovery protocol (LLDP) attributes of interfaces on AlliedWare Plus devices.
author: Cheng Yi Kok (@cyk19)
options:
    config:
        description: A dictionary of LLDP options
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - Full name of the interface
                type: str
                required: True
            receive:
                description:
                    - Enable LLDP reception on interface.
                type: bool
            transmit:
                description:
                    - Enable LLDP transmission on interface
                type: bool
            med_tlv_select:
                description:
                    - Selection of LLDP MED TLVs to send
                    - NOTE, if med-tlv-select is configured idempotency won't be maintained
                      as AlliedWare Plus device doesn't record configured med-tlv-select options is
                      already configured or not from the device side. If you try to apply
                      med-tlv-select option in every play run, Ansible will show changed as True.
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
                      as AlliedWare Plus device doesn't record configured tlv-select options. As
                      such, Ansible cannot verify if the respective tlv-select options is
                      already configured or not from the device side. If you try to applu
                      tlv-select option in every play run, Ansible will show changed as True.
                type: dict
                suboptions:
                    power_management:
                        description:
                              - IEEE 802.3 DTE Power via MDI TLC
                        type: bool
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
notes:
    - Check mode is supported.
"""
EXAMPLES = """
# Using merged
#
# Before state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    Rx --  -- --  001a.eb94.27bb   ---------- -------- -------- McNpLoPe--
#  1.0.3    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--

#
    - name: Merge provided configuration with device configuration
      awplus_lldp_interfaces:
        config:
          - name: port1.0.2
            receive: True
            transmit: True
        state: merged
# After state:
# ------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    Rx Tx  -- --  001a.eb94.27bb   ---------- -------- -------- McNpLoPe--
#  1.0.3    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#


# Using replaced
#
# Before state:
# -------------
#
                                           Optional TLVs Enabled for Tx
 Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
--------------------------------------------------------------------------------
 1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
 1.0.2    Rx Tx  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
 1.0.3    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
 1.0.4    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--

    - name: Replace provided configuration with device configuration
      awplus_lldp_interfaces:
        config:
          - name: port1.0.2
            receive: False
            transmit: True
          - name: port1.0.3
            receive: True
            transmit: False
        state: replaced
# After state:
# ------------
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    -- Tx  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    Rx --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#


# Using overridden
#
# Before state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    Rx Tx  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#
    - name: Override device configuration of all lldp_interfaces with provided configuration
      awplus_lldp_interfaces:
        config:
          - name: port1.0.1
            receive: True
            transmit: True
        state: overridden
# After state:
# ------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    -- --  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--



# Using Deleted
#
# Before state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    Rx Tx  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    Rx --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#
    - name: Delete LLDP attributes of given interfaces
      awplus_lldp_interfaces:
        config:
          - name: port1.0.2
        state: deleted
# After state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    -- --  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    Rx --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--

#


# Using Deleted without any config passed
# "(NOTE: This will delete all of configured LLDP module attributes)"
#
# Before state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    Rx Tx  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    -- --  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    Rx --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#
    - name: Delete LLDP attributes for all configured interfaces
      awplus_lldp_interfaces:
        state: deleted
# After state:
# -------------
#
#                                            Optional TLVs Enabled for Tx
#  Port     Rx/Tx  Notif  Management Addr  Base       802.1    802.3    MED
# --------------------------------------------------------------------------------
#  1.0.1    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.2    -- --  -- --  001a.eb94.27bb   --Sn------ -------- -------- McNpLoPeIn
#  1.0.3    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#  1.0.4    -- --  -- --  192.168.5.2      ---------- -------- -------- McNpLoPe--
#


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
from ansible.module_utils.network.awplus.argspec.lldp_interfaces.lldp_interfaces import Lldp_interfacesArgs
from ansible.module_utils.network.awplus.config.lldp_interfaces.lldp_interfaces import Lldp_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lldp_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Lldp_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
