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
module: pn_dscp_map
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/delete dscp-map
description:
  - This module can be used to create a DSCP priority mapping table.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create dscp-map and
        C(absent) to delete.
    required: True
    type: str
    choices: ["present", "absent"]
  pn_name:
    description:
      - Name for the DSCP map.
    required: False
    type: str
  pn_scope:
    description:
      - Scope for dscp map.
    required: False
    choices: ["local", "fabric"]
"""

EXAMPLES = """
- name: dscp map create
  pn_dscp_map:
    pn_cliswitch: "sw01"
    state: "present"
    pn_name: "foo"
    pn_scope: "local"

- name: dscp map delete
  pn_dscp_map:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_name: "foo"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the dscp-map command.
  returned: always
  type: list
stderr:
  description: set of error responses from the dscp-map command.
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
    This method checks for idempotency using the dscp-map-show name command.
    If a user with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']

    cli += ' dscp-map-show name %s format name no-show-headers' % name
    out = run_commands(module, cli)[1]

    out = out.split()

    return True if name in out[-1] else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='dscp-map-create',
        absent='dscp-map-delete'
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
        )
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

    if command == 'dscp-map-delete':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='dscp map with name %s does not exist' % name
            )
    else:
        if command == 'dscp-map-create':
            if NAME_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='dscp map with name %s already exists' % name
                )

        if scope:
            cli += ' scope ' + scope

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
