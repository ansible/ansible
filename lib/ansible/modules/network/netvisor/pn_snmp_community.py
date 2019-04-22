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
module: pn_snmp_community
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete snmp-community
description:
  - This module can be used to create SNMP communities for SNMPv1 or
    delete SNMP communities for SNMPv1 or modify SNMP communities for SNMPv1.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
  state:
    description:
      - State the action to perform. Use C(present) to create snmp-community and
        C(absent) to delete snmp-community C(update) to update snmp-community.
    required: true
    type: str
    choices: ['present', 'absent', 'update']
  pn_community_type:
    description:
      - community type.
    type: str
    choices: ['read-only', 'read-write']
  pn_community_string:
    description:
      - community name.
    type: str
"""

EXAMPLES = """
- name: Create snmp community
  pn_snmp_community:
    pn_cliswitch: "sw01"
    state: "present"
    pn_community_string: "foo"
    pn_community_type: "read-write"

- name: Delete snmp community
  pn_snmp_community:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_community_string: "foo"

- name: Modify snmp community
  pn_snmp_community:
    pn_cliswitch: "sw01"
    state: "update"
    pn_community_string: "foo"
    pn_community_type: "read-only"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the snmp-community command.
  returned: always
  type: list
stderr:
  description: set of error responses from the snmp-community command.
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


def check_cli(module, cli):
    """
    This method checks for idempotency using the snmp-community-show command.
    If a user with given name exists, return as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    comm_str = module.params['pn_community_string']

    cli += ' snmp-community-show format community-string no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if comm_str in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='snmp-community-create',
        absent='snmp-community-delete',
        update='snmp-community-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_community_type=dict(required=False, type='str',
                                   choices=['read-only', 'read-write']),
            pn_community_string=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_community_type", "pn_community_string"]],
            ["state", "absent", ["pn_community_string"]],
            ["state", "update", ["pn_community_type", "pn_community_string"]],
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    community_type = module.params['pn_community_type']
    comm_str = module.params['pn_community_string']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    COMMUNITY_EXISTS = check_cli(module, cli)

    if command == 'snmp-community-modify':
        if COMMUNITY_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='snmp community name %s does not exist' % comm_str
            )

    if command == 'snmp-community-delete':
        if COMMUNITY_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='snmp community name %s does not exist' % comm_str
            )

    if command == 'snmp-community-create':
        if COMMUNITY_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='snmp community with name %s already exists' % comm_str
            )

    cli += ' %s community-string %s ' % (command, comm_str)

    if command != 'snmp-community-delete' and community_type:
        cli += ' community-type ' + community_type

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
