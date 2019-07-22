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
module: pn_access_list
author: "Pluribus Networks (@amitsi)"
version_added: "2.8"
short_description: CLI command to create/delete access-list
description:
  - This module can be used to create and delete an access list.
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
      - Access List Name.
    required: false
    type: str
  pn_scope:
    description:
      - 'scope. Available valid values - local or fabric.'
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
  type: str
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module, cli):
    """
    This method checks for idempotency using the access-list-show command.
    If a list with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    list_name = module.params['pn_name']

    cli += ' access-list-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if list_name in out else False


def main():
    """ This section is for arguments parsing """

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

    ACC_LIST_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, list_name)

    if command == 'access-list-delete':
        if ACC_LIST_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='access-list with name %s does not exist' % list_name
            )
    else:
        if command == 'access-list-create':
            if ACC_LIST_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='access list with name %s already exists' % list_name
                )
        cli += ' scope %s ' % scope

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
