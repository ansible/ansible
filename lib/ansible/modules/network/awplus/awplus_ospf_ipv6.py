#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network',
}


DOCUMENTATION = """
---
module: awplus_ospf
version_added: "2.10"
short_description: Manages IPv6 OSPF configuration.
description:
    - Manages IPv6 OSPF configurations on AlliedWare Plus switches.
author:
    - Isaac Daly (@dalyIsaac)
notes:
    - C(state=present) is the default for all state options.
options:
  router:
    description:
        - This configures the router to use OSPF.
    suboptions:
        state:
            description:
                - C(state=absent) is used to terminate and delete a specific OSPF
                  routing process.
            choices: ['present', 'absent']
        process_id:
            description:
                - A positive integer in the range 1 to 65535 used to define a routing
                  process.
    required: True
notes:
    - Check mode is supported.
"""


EXAMPLES = """
commands:
    - name: Configure OSPF IPv6 router process id
        awplus_ospf_ipv6:
            router:
                process_id: 100
"""


RETURN = """
commands:
    description: The list of commands to send to the device
    returned: always
    type: list
    sample: ['router ipv6 ospf']
"""

from ansible.module_utils.network.awplus.utils.complex_constructor import (
    PRESENT,
    STATE,
    ABSENT,
    get_commands,
)
from ansible.module_utils.network.awplus.awplus import (
    get_config,
    load_config,
    awplus_argument_spec,
)
from ansible.module_utils.basic import AnsibleModule


KEY_TO_COMMAND_MAP = {}


def _append(cmd, state, val):
    if state == PRESENT and val is not None:
        return cmd + ' {}'.format(val)
    return cmd


def router_ospf_map(module, commands):
    params = module.params['router']
    cmd = 'router ipv6 ospf'
    state = params[STATE]

    process_id = params.get('process_id')

    if process_id:
        cmd += ' {}'.format(process_id)
    if state == ABSENT and len(commands) == 0:
        return 'no ' + cmd
    return cmd


def get_existing_config(module):
    config = (get_config(module, flags=[' router ipv6 ospf']),)

    existing_config = set()
    ospf = None
    for item in config:
        for line in item.splitlines():
            s = line.strip()
            existing_config.add(s)
            if 'router ipv6 ospf' in s:
                ospf = s

    return ospf, existing_config


def main():
    router_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'process_id': {'type': 'int'},
        'vrf_instance': {'type': 'str'},
    }

    argument_spec = {
        'router': {'type': 'dict', 'options': router_spec, 'required': True},
    }

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    warnings = []
    result = {'changed': False, 'warnings': warnings}

    ospf, existing_config = get_existing_config(module)
    commands = get_commands(
        module, KEY_TO_COMMAND_MAP, router_ospf_map, ospf, existing_config
    )
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
