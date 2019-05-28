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
module: pn_role
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/delete/modify role
description:
  - This module can be used to create, delete and modify user roles.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create role and
        C(absent) to delete role and C(update) to modify role.
    required: true
    type: str
    choices: ['present', 'absent', 'update']
  pn_scope:
    description:
      - local or fabric.
    required: false
    type: str
    choices: ['local', 'fabric']
  pn_access:
    description:
      - type of access.
    required: false
    type: str
    choices: ['read-only', 'read-write']
  pn_shell:
    description:
      - allow shell command.
    required: false
    type: bool
  pn_sudo:
    description:
      - allow sudo from shell.
    required: false
    type: bool
  pn_running_config:
    description:
      - display running configuration of switch.
    required: false
    type: bool
  pn_name:
    description:
      - role name.
    required: true
    type: str
  pn_delete_from_users:
    description:
      - delete from users.
    required: false
    type: bool
"""

EXAMPLES = """
- name: Role create
  pn_role:
    pn_cliswitch: 'sw01'
    state: 'present'
    pn_name: 'foo'
    pn_scope: 'local'
    pn_access: 'read-only'

- name: Role delete
  pn_role:
    pn_cliswitch: 'sw01'
    state: 'absent'
    pn_name: 'foo'

- name: Role modify
  pn_role:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_name: 'foo'
    pn_access: 'read-write'
    pn_sudo: true
    pn_shell: true
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the role command.
  returned: always
  type: list
stderr:
  description: set of error responses from the role command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module, cli):
    """
    This method checks for idempotency using the role-show command.
    If a role with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    role_name = module.params['pn_name']

    cli += ' role-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if role_name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='role-create',
        absent='role-delete',
        update='role-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_access=dict(required=False, type='str',
                           choices=['read-only', 'read-write']),
            pn_shell=dict(required=False, type='bool'),
            pn_sudo=dict(required=False, type='bool'),
            pn_running_config=dict(required=False, type='bool'),
            pn_name=dict(required=False, type='str'),
            pn_delete_from_users=dict(required=False, type='bool'),
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_scope"]],
            ["state", "absent", ["pn_name"]],
            ["state", "update", ["pn_name"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    scope = module.params['pn_scope']
    access = module.params['pn_access']
    shell = module.params['pn_shell']
    sudo = module.params['pn_sudo']
    running_config = module.params['pn_running_config']
    name = module.params['pn_name']
    delete_from_users = module.params['pn_delete_from_users']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    ROLE_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if shell is (False or '') and sudo is True:
        module.fail_json(
            failed=True,
            msg='sudo access requires shell access'
        )

    if command == 'role-modify':
        if ROLE_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='Role with name %s does not exist' % name
            )

    if command == 'role-delete':
        if ROLE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Role with name %s does not exist' % name
            )

    if command == 'role-create':
        if ROLE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Role with name %s already exists' % name
            )

        if scope:
            cli += ' scope ' + scope

    if command != 'role-delete':
        if access:
            cli += ' access ' + access

        cli += booleanArgs(shell, 'shell', 'no-shell')
        cli += booleanArgs(sudo, 'sudo', 'no-sudo')
        cli += booleanArgs(running_config, 'running-config', 'no-running-config')

    if command == 'role-modify':
        if delete_from_users:
            cli += ' delete-from-users ' + delete_from_users

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
