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
module: pn_user
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete user
description:
  - This module can be used to create a user and apply a role,
    update a user and delete a user.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    type: str
    required: false
  state:
    description:
      - State the action to perform. Use C(present) to create user and
        C(absent) to delete user C(update) to update user.
    type: str
    required: true
    choices: ['present', 'absent', 'update']
  pn_scope:
    description:
      - local or fabric.
    type: str
    choices: ['local', 'fabric']
  pn_initial_role:
    description:
      - initial role for user.
    type: str
  pn_password:
    description:
      - plain text password.
    type: str
  pn_name:
    description:
      - username.
    type: str
"""

EXAMPLES = """
- name: Create user
  pn_user:
    pn_cliswitch: "sw01"
    state: "present"
    pn_scope: "fabric"
    pn_password: "foo123"
    pn_name: "foo"

- name: Delete user
  pn_user:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_name: "foo"

- name: Modify user
  pn_user:
    pn_cliswitch: "sw01"
    state: "update"
    pn_password: "test1234"
    pn_name: "foo"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the user command.
  returned: always
  type: list
stderr:
  description: set of error responses from the user command.
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
    This method checks for idempotency using the user-show command.
    If a user already exists on the given switch, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']

    cli += ' user-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='user-create',
        absent='user-delete',
        update='user-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_initial_role=dict(required=False, type='str'),
            pn_password=dict(required=False, type='str', no_log=True),
            pn_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_scope"]],
            ["state", "absent", ["pn_name"]],
            ["state", "update", ["pn_name", "pn_password"]]
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    scope = module.params['pn_scope']
    initial_role = module.params['pn_initial_role']
    password = module.params['pn_password']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    USER_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'user-modify':
        if USER_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='User with name %s does not exist' % name
            )
        if initial_role or scope:
            module.fail_json(
                failed=True,
                msg='Only password can be modified'
            )

    if command == 'user-delete':
        if USER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='user with name %s does not exist' % name
            )

    if command == 'user-create':
        if USER_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='User with name %s already exists' % name
            )
        if scope:
            cli += ' scope ' + scope

        if initial_role:
            cli += ' initial-role ' + initial_role

    if command != 'user-delete':
        if password:
            cli += ' password ' + password

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
