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
version_added: "2.10"
short_description: Manage Static Link Aggregation on AlliedWare Plus devices.
description: This module manages properties of Static Link Aggregation Group on AlliedWare Plus devices.
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
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
                    member_filters:
                        description:
                            - Allow QoS and ACL settings to be configured on aggregator's individual member ports
                        type: bool
                        default: False
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
notes:
    - Check mode is supported.
"""

EXAMPLES = """
- name: Merge provided configuration with device configuration
    awplus_lag_interfaces:
        config:
            - name: 10
                members:
                    - member: port1.0.4
                        member_filters: True
                    - member: port1.0.3
        state: merged
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

from ansible.module_utils.network.awplus.config.static_lag_interfaces.static_lag_interfaces import Static_Lag_interfaces
from ansible.module_utils.network.awplus.argspec.static_lag_interfaces.static_lag_interfaces import Static_Lag_interfacesArgs
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Static_Lag_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Static_Lag_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
