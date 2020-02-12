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
module: awplus_vlans
version_added: "2.10"
short_description: Manage VLANs on AlliedWare Plus devices.
description: This module provides declarative management of VLANs on AlliedWare Plus devices
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
options:
    config:
        description: A dictionary of VLANs options
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - ASCII name of the VLAN
                    - NOTE, I(name) should not be named/appended with I(default) as it is reserved for device default vlans.
                type: str
            vlan_id:
                description:
                    - ID of the VLAN. Range 1-4094
                type: int
                required: True
            state:
                description:
                    - Operational state of the VLAN
                type: str
                choices:
                    - enable
                    - disable
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
# Before state:
# -------------
#
# aw1>show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u)
# 2       vlan2            STATIC  SUSPEND port1.0.2(u)
# 3       vlan3            STATIC  SUSPEND
# 20      VLAN0020         STATIC  ACTIVE  port1.0.3(t)
# 21      VLAN0021         STATIC  ACTIVE  port1.0.3(t)
# 22      VLAN0022         STATIC  ACTIVE  port1.0.3(t)
# 23      VLAN0023         STATIC  ACTIVE  port1.0.3(t)
# 24      VLAN0024         STATIC  ACTIVE  port1.0.3(t)
# 25      VLAN0025         STATIC  ACTIVE  port1.0.3(t) port1.0.4(u)
# 40      VLAN0040         STATIC  ACTIVE  port1.0.3(u)
# 100     testing1         STATIC  ACTIVE
    - name: Merge
      awplus_vlans:
        config:
          - name: testing2
            state: disable
            vlan_id: 100
        state: merged
# After state:
# ------------
#
# aw1>show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u)
# 2       vlan2            STATIC  SUSPEND port1.0.2(u)
# 3       vlan3            STATIC  SUSPEND
# 20      VLAN0020         STATIC  ACTIVE  port1.0.3(t)
# 21      VLAN0021         STATIC  ACTIVE  port1.0.3(t)
# 22      VLAN0022         STATIC  ACTIVE  port1.0.3(t)
# 23      VLAN0023         STATIC  ACTIVE  port1.0.3(t)
# 24      VLAN0024         STATIC  ACTIVE  port1.0.3(t)
# 25      VLAN0025         STATIC  ACTIVE  port1.0.3(t) port1.0.4(u)
# 40      VLAN0040         STATIC  ACTIVE  port1.0.3(u)
# 100     testing2         STATIC  SUSPEND


# Using overridden
# Before state:
# -------------
#
# aw1>show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u)
# 2       vlan2            STATIC  SUSPEND port1.0.2(u)
# 3       vlan3            STATIC  SUSPEND
# 20      VLAN0020         STATIC  ACTIVE  port1.0.3(t)
# 21      VLAN0021         STATIC  ACTIVE  port1.0.3(t)
# 22      VLAN0022         STATIC  ACTIVE  port1.0.3(t)
# 23      VLAN0023         STATIC  ACTIVE  port1.0.3(t)
# 24      VLAN0024         STATIC  ACTIVE  port1.0.3(t)
# 25      VLAN0025         STATIC  ACTIVE  port1.0.3(t) port1.0.4(u)
# 40      VLAN0040         STATIC  ACTIVE  port1.0.3(u)
# 100     testing2         STATIC  SUSPEND
- name: Override device configuration of all VLANs with provided configuration
  awplus_vlans:
    config:
      - name: vlan2
        vlan_id: 2
        state: enable
    state: overridden
# After state:
# ------------
#
# aw1>show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u) port1.0.3(u) port1.0.4(u)
# 2       vlan2            STATIC  ACTIVE  port1.0.2(u)


# Using replaced
# Before state:
# -------------
#
# aw1#show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u) port1.0.3(u) port1.0.4(u)
# 2       vlan2            STATIC  ACTIVE  port1.0.2(u)
# 3       VLAN0003         STATIC  ACTIVE
# 20      VLAN0020         STATIC  ACTIVE
# 21      VLAN0021         STATIC  ACTIVE
# 22      VLAN0022         STATIC  ACTIVE
# 23      VLAN0023         STATIC  ACTIVE
# 24      VLAN0024         STATIC  ACTIVE
# 25      VLAN0025         STATIC  ACTIVE
# 40      VLAN0040         STATIC  ACTIVE
# 100     VLAN0100         STATIC  ACTIVE
    - name: Replaces device configuration of listed VLANS with provided configuration
      awplus_vlans:
        config:
          - vlan_id: 100
            name: Test_VLAN100
            state: disable
        state: replaced
# After state:
# ------------
#
# aw1#show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u) port1.0.3(u) port1.0.4(u)
# 2       vlan2            STATIC  ACTIVE  port1.0.2(u)
# 3       VLAN0003         STATIC  ACTIVE
# 20      VLAN0020         STATIC  ACTIVE
# 21      VLAN0021         STATIC  ACTIVE
# 22      VLAN0022         STATIC  ACTIVE
# 23      VLAN0023         STATIC  ACTIVE
# 24      VLAN0024         STATIC  ACTIVE
# 25      VLAN0025         STATIC  ACTIVE
# 40      VLAN0040         STATIC  ACTIVE
# 100     Test_VLAN100     STATIC  ACTIVE


# Using deleted
# Before state:
# -------------
#
# aw1#show vlan all
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u) port1.0.3(u) port1.0.4(u)
# 2       vlan2            STATIC  ACTIVE  port1.0.2(u)
# 3       VLAN0003         STATIC  ACTIVE
# 20      VLAN0020         STATIC  ACTIVE
# 21      VLAN0021         STATIC  ACTIVE
# 22      VLAN0022         STATIC  ACTIVE
# 23      VLAN0023         STATIC  ACTIVE
# 24      VLAN0024         STATIC  ACTIVE
# 25      VLAN0025         STATIC  ACTIVE
# 40      VLAN0040         STATIC  ACTIVE
# 100     Test_VLAN100     STATIC  ACTIVE
    - name: Delete attributes of given VLANs
      awplus_vlans:
        config:
          - vlan_id: 100
        state: deleted
# After state:
# -------------
#
# aw1#show vlan al
# VLAN ID  Name            Type    State   Member ports
#                                          (u)-Untagged, (t)-Tagged
# ======= ================ ======= ======= ====================================
# 1       default          STATIC  ACTIVE  port1.0.1(u) port1.0.3(u) port1.0.4(u)
# 2       vlan2            STATIC  ACTIVE  port1.0.2(u)
# 3       VLAN0003         STATIC  ACTIVE
# 20      VLAN0020         STATIC  ACTIVE
# 21      VLAN0021         STATIC  ACTIVE
# 22      VLAN0022         STATIC  ACTIVE
# 23      VLAN0023         STATIC  ACTIVE
# 24      VLAN0024         STATIC  ACTIVE
# 25      VLAN0025         STATIC  ACTIVE
# 40      VLAN0040         STATIC  ACTIVE
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

from ansible.module_utils.network.awplus.config.vlans.vlans import Vlans
from ansible.module_utils.network.awplus.argspec.vlans.vlans import VlansArgs
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=VlansArgs.argument_spec,
                           supports_check_mode=True)

    result = Vlans(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
