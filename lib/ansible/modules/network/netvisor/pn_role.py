#!/usr/bin/python
""" PN CLI role-create/delete """
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_role
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/delete role.
description:
  - C(create): create user roles
  - C(delete): delete user roles
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
  state:
    description:
      - State the action to perform. Use 'present' to create role and
        'absent' to delete role and 'update' to modify role.
    required: True
  pn_scope:
    description:
      - local or fabric
    required: false
    choices: ['local', 'fabric']
  pn_access:
    description:
      - type of access - default read-write
    required: false
    choices: ['read-only', 'read-write']
  pn_shell:
    description:
      - allow shell command
    required: false
  pn_sudo:
    description:
      - allow sudo from shell
    required: false
  pn_running_config:
    description:
      - display running configuration of switch
    required: false
  pn_name:
    description:
      - role name
    required: True
  pn_delete_from_users:
    description:
      - delete from users
    required: false
"""

EXAMPLES = """
- name: role functionality
  pn_role:
    pn_cliswitch: "sw01"
    state: 'present'
    pn_name: 'enss'
    pn_scope: 'local'

- name: role functionality
  pn_role:
    pn_cliswitch: "sw01"
    state: 'absent'
    pn_name: 'enss'

- name: role functionality
  pn_role:
    pn_cliswitch: "sw01"
    state: "update"
    pn_name: "enss"
    pn_sudo: True
"""

RETURN = """
command:
  description: the CLI command run on the target node.
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


import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli
from ansible.module_utils.pn_nvos import booleanArgs

ROLE_EXISTS = None


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    state = module.params['state']
    command = state_map[state]

    cmd = shlex.split(cli)
    result, out, err = module.run_command(cmd)

    remove_cmd = '/usr/bin/cli --quiet -e --no-login-prompt'

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            msg="%s operation completed" % command,
            changed=True
        )


def check_cli(module, cli):
    """
    This method checks for idempotency using the role-show command.
    If a role with given name exists, return ROLE_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: ROLE_EXISTS
    """
    role_name = module.params['pn_name']

    show = cli + \
        ' role-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()

    # Global flags
    global ROLE_EXISTS
    ROLE_EXISTS = True if role_name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
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

    check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if shell is False and sudo is True:
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
            cli += ' delete-from-users '

    run_cli(module, cli)


if __name__ == '__main__':
    main()
