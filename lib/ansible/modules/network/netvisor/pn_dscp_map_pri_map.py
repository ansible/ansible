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
module: pn_dscp_map_pri_map
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify dscp-map-pri-map
description:
  - This module can be used to update priority mappings in tables.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify
        the dscp-map-pri-map.
    required: True
    type: str
    choices: ['update']
  pn_pri:
    description:
      - CoS priority.
    required: False
    type: str
  pn_name:
    description:
      - Name for the DSCP map.
    required: False
    type: str
  pn_dsmap:
    description:
      - DSCP value(s).
    required: False
    type: str
"""

EXAMPLES = """
- name: dscp map pri map modify
  pn_dscp_map_pri_map:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_name: 'foo'
    pn_pri: '0'
    pn_dsmap: '40'

- name: dscp map pri map modify
  pn_dscp_map_pri_map:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_name: 'foo'
    pn_pri: '1'
    pn_dsmap: '8,10,12,14'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the dscp-map-pri-map command.
  returned: always
  type: list
stderr:
  description: set of error responses from the dscp-map-pri-map command.
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

    cli += ' dscp-map-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='dscp-map-pri-map-modify'
    )
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_pri=dict(required=False, type='str'),
            pn_name=dict(required=False, type='str'),
            pn_dsmap=dict(required=False, type='str'),
        ),
        required_if=(
            ['state', 'update', ['pn_name', 'pn_pri']],
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    pri = module.params['pn_pri']
    name = module.params['pn_name']
    dsmap = module.params['pn_dsmap']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)

    if command == 'dscp-map-pri-map-modify':
        if NAME_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='Create dscp map with name %s before updating' % name
            )
        cli += ' %s ' % command
        if pri:
            cli += ' pri ' + pri
        if name:
            cli += ' name ' + name
        if dsmap:
            cli += ' dsmap ' + dsmap

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
