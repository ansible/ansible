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
module: awplus_lacp
author: Cheng Yi Kok (@cyk19)
short_description: Mange Global Link Aggregation Control Protocol (LACP) on AlliedWare Plus devices.
description: This module provides declarative management of Global LACP on AlliedWare Plus network devices.
version_added: "2.10"
options:
  config:
    description: The provided configurations
    type: dict
    sub options:
      system:
        description: This option sets the default system parameters for LACP.
        type: dict
        sub options:
          priority:
            description:
              - LACP priority for the system.
              - Refer to vendor documentation for valid values.
            type: int
            required: True
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
# Using merged
#
# Before state:
# -------------
#
# aw1#show lacp sys-id
# System Priority: 0x8000 (32768)
# MAC Address: 001a.eb94.27bb
  - name: Merge provided configuration with device configuration
    awplus_lacp:
      config:
        system:
          priority: 123
      state: merged
# After state:
# ------------
#
# aw1#show lacp sys-id
# System Priority: 0x007b (123)
# MAC Address: 001a.eb94.27bb

# Using Deleted
#
# Before state:
# -------------
#
# aw1#show lacp sys-id
# System Priority: 0x007b (123)
# MAC Address: 001a.eb94.27bb
- name: Delete global lacp attribute
  awplus_lacp:
    state: deleted
# After state:
# -------------
#
# aw1#show lacp sys-id
# System Priority: 0x8000 (32768)
# MAC Address: 001a.eb94.27bb

# Using replaced
#
# Before state:
# -------------
#
# aw1#show lacp sys-id
# System Priority: 0x8000 (32768)
# MAC Address: 001a.eb94.27bb
  - name: Replaces global LACP configuration
    awplus_lacp:
      config:
        system:
          priority: 50
      state: replaced
# After state:
# ------------
#
# System Priority: 0x0032 (50)
# MAC Address: 001a.eb94.27bb

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
from ansible.module_utils.network.awplus.argspec.lacp.lacp import LacpArgs
from ansible.module_utils.network.awplus.config.lacp.lacp import Lacp


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=LacpArgs.argument_spec,
                           supports_check_mode=True)

    result = Lacp(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
