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
module: pn_prefix_list
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to create/delete prefix-list
description:
  - This module can be used to create or delete prefix list.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create prefix-list and
        C(absent) to delete prefix-list.
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  pn_name:
    description:
      - Prefix List Name.
    required: true
    type: str
  pn_scope:
    description:
      - scope of prefix-list.
    required: false
    type: str
    choices: ['local', 'fabric']
"""

EXAMPLES = """
- name: Create prefix list
  pn_prefix_list:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_scope: "local"
    state: "present"

- name: Delete prefix list
  pn_prefix_list:
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
  description: set of responses from the prefix-list command.
  returned: always
  type: list
stderr:
  description: set of error responses from the prefix-list command.
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
    This method checks for idempotency using the prefix-list-show command.
    If a name exists, return True if name exists else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']

    cli += ' prefix-list-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='prefix-list-create',
        absent='prefix-list-delete'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str',
                   choices=state_map.keys(), default='present'),
        pn_name=dict(required=True, type='str'),
        pn_scope=dict(required=False, type='str',
                      choices=['local', 'fabric']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ["pn_name", "pn_scope"]],
            ["state", "absent", ["pn_name"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    name = module.params['pn_name']
    scope = module.params['pn_scope']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)

    cli += ' %s name %s ' % (command, name)

    if command == 'prefix-list-delete':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='prefix-list with name %s does not exist' % name
            )
    else:
        if command == 'prefix-list-create':
            if NAME_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='prefix list with name %s already exists' % name
                )
        cli += ' scope %s ' % scope

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
