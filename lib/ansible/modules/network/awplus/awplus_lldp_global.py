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
module: awplus_lldp_global
author: Cheng Yi Kok (@cyk19)
short_description: Configure and manage Link Layer Discovery Protocol(LLDP) attributes on AlliedWare Plus devices
description: This module configures and manages the Link Layer Discovery Protocol (LLDP) attributes on AlliedWare Plus platforms.
version_added: "2.10"
options:
  config:
    description: A dictionary of LLDP options
    type: dict
    suboptions:
      holdtime:
        description:
          - LLDP holdtime (in sec) to be sent in packets.
          - Refer to vendor documentation for valid values.
        type: int
      reinit:
        description:
          - Specify the delay (in secs) for LLDP to initialize.
          - Refer to vendor documentation for valid values.
          - NOTE, if LLDP reinit is configured with a starting
            value, idempotency won't be maintained as the AlliedWare Plus
            device doesn't record the starting reinit configured
            value. As such, Ansible cannot verify if the respective
            starting reinit value is already configured or not from
            the device side. If you try to apply starting reinit
            value in every play run, Ansible will show changed as True.
            For any other reinit value, idempotency will be maintained
            since any other reinit value is recorded in the AlliedWare Plus device.
        type: int
      enabled:
        description:
          - Enable LLDP
        type: bool
      timer:
        description:
          - Specify the rate at which LLDP packets are sent (in sec).
          - Refer to vendor documentation for valid values.
        type: int
  state:
    description:
    - The state of the configuration after module completion
    type: str
    choices:
    - merged
    - replaced
    - deleted
    default: merged
"""

EXAMPLES = """
# Before state:
# -------------
# aw1#sh lldp

# LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Enabled     [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 30 secs     [30]
#   Hold-time Multiplier ...... 4           [4]
#   (Computed TTL value ....... 120 secs)
#   Reinitialization Delay .... 2 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]

    - name: Merge provided congfiguration with device configuration
      awplus_lldp_global:
        config:
          holdtime: 10
          enabled: True
          reinit: 3
          timer: 10
        state: merged
# After state:
# ------------
# aw1#sh lldp

# LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Enabled     [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 10 secs     [30]
#   Hold-time Multiplier ...... 10          [4]
#   (Computed TTL value ....... 100 secs)
#   Reinitialization Delay .... 3 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]

# Using replaced
# Before state:
# -------------
LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Enabled    [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 30 secs     [30]
#   Hold-time Multiplier ...... 10          [4]
#   (Computed TTL value ....... 120 secs)
#   Reinitialization Delay .... 3 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]
    - name: Replaces LLDP device configuration with provided configuration
      awplus_lldp_global:
        config:
          holdtime: 4
          reinit: 5
        state: replaced

# After state:
# -------------
# LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Disabled    [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 30 secs     [30]
#   Hold-time Multiplier ...... 4           [4]
#   (Computed TTL value ....... 120 secs)
#   Reinitialization Delay .... 5 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]

# Using Deleted without any config passed
#"(NOTE: This will delete all of configured LLDP module attributes)"
# Before state:
# -------------
# LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Disabled    [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 30 secs     [30]
#   Hold-time Multiplier ...... 4           [4]
#   (Computed TTL value ....... 120 secs)
#   Reinitialization Delay .... 5 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]
    - name: Delete LLDP attributes
      awplus_lldp_global:
        state: deleted

# After state:
# -------------
# aw1#sh lldp

# LLDP Global Configuration:                [Default Values]
#   LLDP Status ............... Disabled    [Disabled]
#   Notification Interval ..... 5 secs      [5]
#   Tx Timer Interval ......... 30 secs     [30]
#   Hold-time Multiplier ...... 4           [4]
#   (Computed TTL value ....... 120 secs)
#   Reinitialization Delay .... 2 secs      [2]
#   Tx Delay .................. 2 secs      [2]
#   Port Number Type .......... Port-Number [Port-Number]
#   Fast Start Count .......... 3           [3]
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
from ansible.module_utils.network.awplus.argspec.lldp_global.lldp_global import Lldp_globalArgs
from ansible.module_utils.network.awplus.config.lldp_global.lldp_global import Lldp_global


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lldp_globalArgs.argument_spec,
                           supports_check_mode=True)

    result = Lldp_global(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
