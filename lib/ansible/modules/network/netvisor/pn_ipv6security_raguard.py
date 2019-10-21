#!/usr/bin/python
# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_ipv6security_raguard
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to create/modify/delete ipv6security-raguard
description:
  - This module can be used to add ipv6 RA Guard Policy, Update ipv6 RA guard Policy and Remove ipv6 RA Guard Policy.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - ipv6security-raguard configuration command.
    required: false
    choices: ['present', 'update', 'absent']
    type: str
    default: 'present'
  pn_device:
    description:
      - RA Guard Device. host or router.
    required: false
    choices: ['host', 'router']
    type: str
  pn_access_list:
    description:
      - RA Guard Access List of Source IPs.
    required: false
    type: str
  pn_prefix_list:
    description:
      - RA Guard Prefix List.
    required: false
    type: str
  pn_router_priority:
    description:
      - RA Guard Router Priority.
    required: false
    type: str
    choices: ['low', 'medium', 'high']
  pn_name:
    description:
      - RA Guard Policy Name.
    required: true
    type: str
"""

EXAMPLES = """
- name: ipv6 security ragurad create
  pn_ipv6security_raguard:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_device: "host"

- name: ipv6 security ragurad create
  pn_ipv6security_raguard:
    pn_cliswitch: "sw01"
    pn_name: "foo1"
    pn_device: "host"
    pn_access_list: "sample"
    pn_prefix_list: "sample"
    pn_router_priority: "low"

- name: ipv6 security ragurad modify
  pn_ipv6security_raguard:
    pn_cliswitch: "sw01"
    pn_name: "foo1"
    pn_device: "router"
    pn_router_priority: "medium"
    state: "update"

- name: ipv6 security ragurad delete
  pn_ipv6security_raguard:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    state: "absent"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the ipv6security-raguard command.
  returned: always
  type: list
stderr:
  description: set of error responses from the ipv6security-raguard command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module):
    """
    This method checks for idempotency using the ipv6security-raguard-show command.
    If a name exists, return True if name exists else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']

    cli = 'ipv6security-raguard-show format name parsable-delim ,'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def check_list(module, list_name, command):
    """
    This method checks for idempotency using provided command.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """

    cli = '%s format name no-show-headers' % command
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    if list_name not in out:
        module.fail_json(
            failed=True,
            msg='%s name %s does not exists' % (command, list_name)
        )


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='ipv6security-raguard-create',
        absent='ipv6security-raguard-delete',
        update='ipv6security-raguard-modify'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_device=dict(required=False, type='str', choices=['host', 'router']),
        pn_access_list=dict(required=False, type='str'),
        pn_prefix_list=dict(required=False, type='str'),
        pn_router_priority=dict(required=False, type='str', choices=['low', 'medium', 'high']),
        pn_name=dict(required=True, type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ['pn_device']],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    device = module.params['pn_device']
    access_list = module.params['pn_access_list']
    prefix_list = module.params['pn_prefix_list']
    router_priority = module.params['pn_router_priority']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module)

    if command == 'ipv6security-raguard-modify':
        if not device and not access_list and not prefix_list and not router_priority:
            module.fail_json(
                failed=True,
                msg='required one of device, access_list, prefix_list or router_priority'
            )

    if command == 'ipv6security-raguard-create':
        if NAME_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='ipv6 security raguard with name %s already exists' % name
            )

    if command != 'ipv6security-raguard-create':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='ipv6 security raguard with name %s does not exist' % name
            )

    cli += ' %s name %s ' % (command, name)
    if command != 'ipv6security-raguard-delete':
        if device == 'router':
            cli += ' device ' + device
            if access_list:
                check_list(module, access_list, 'access-list-show')
                cli += ' access-list ' + access_list
            if prefix_list:
                check_list(module, prefix_list, 'prefix-list-show')
                cli += ' prefix-list ' + prefix_list
            if router_priority:
                cli += ' router-priority ' + router_priority
        if device == 'host':
            cli += ' device ' + device

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
