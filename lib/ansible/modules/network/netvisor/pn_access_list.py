#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_access_list
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.8"
short_description: CLI command to create/delete access-list.
description:
  - create and delete an access list
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to create access-list and
        'absent' to delete access-list.
    required: True
    choices: [ "present", "absent"]
  pn_name:
    description:
      - Access List Name
    required: false
    type: str
  pn_scope:
    description:
      - scope - local or fabric
    required: false
    choices: ['local', 'fabric']
"""

EXAMPLES = """
- name: access list functionality
  pn_access_list:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_scope: "local"
    state: "present"

- name: access list functionality
  pn_access_list:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_scope: "local"
    state: "absent"

- name: access list functionality
  pn_access_list:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_scope: "fabric"
    state: "present"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: string
stdout:
  description: set of responses from the access-list command.
  returned: always
  type: list
stderr:
  description: set of error responses from the access-list command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli


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
    This method checks for idempotency using the access-list-show command.
    If a list with given name exists, return ACC_LIST_EXISTS
    as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: ACC_LIST_EXISTS
    """
    list_name = module.params['pn_name']

    show = cli + \
        ' access-list-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global ACC_LIST_EXISTS

    ACC_LIST_EXISTS = True if list_name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        present='access-list-create',
        absent='access-list-delete',
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_name=dict(required=False, type='str'),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_scope"]],
            ["state", "absent", ["pn_name"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    list_name = module.params['pn_name']
    scope = module.params['pn_scope']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    check_cli(module, cli)
    cli += ' %s name %s ' % (command, list_name)

    if command == 'access-list-delete':
        if ACC_LIST_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='access-list with name %s does not exist' % list_name
            )
    else:
        if command == 'access-list-create':
            check_cli(module, cli)
            if ACC_LIST_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='access list with name %s already exists' % list_name
                )
        cli += ' scope %s ' % scope

    run_cli(module, cli)


if __name__ == '__main__':
    main()
