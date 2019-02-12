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
module: pn_vflow_table_profile
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify vflow-table-profile
description:
  - This module can be used to modify a vFlow table profile.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify
        the vflow-table-profile.
    required: true
    type: str
    choices: ['update']
  pn_profile:
    description:
      - type of vFlow profile.
    required: false
    type: str
    choices: ['application', 'ipv6', 'qos']
  pn_hw_tbl:
    description:
      - hardware table used by vFlow.
    required: false
    type: str
    choices: ['switch-main', 'switch-hash', 'npu-main', 'npu-hash']
  pn_enable:
    description:
      - enable or disable vflow profile table.
    required: false
    type: bool
"""

EXAMPLES = """
- name: Modify vflow table profile
  pn_vflow_table_profile:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_profile: 'ipv6'
    pn_hw_tbl: 'switch-main'
    pn_enable: true

- name: Modify vflow table profile
  pn_vflow_table_profile:
    state: 'update'
    pn_profile: 'qos'
    pn_hw_tbl: 'switch-main'
    pn_enable: false
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vflow-table-profile command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vflow-table-profile command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='vflow-table-profile-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_profile=dict(required=False, type='str',
                            choices=['application', 'ipv6', 'qos']),
            pn_hw_tbl=dict(required=False, type='str',
                           choices=['switch-main', 'switch-hash',
                                    'npu-main', 'npu-hash']),
            pn_enable=dict(required=False, type='bool'),
        ),
        required_if=(
            ['state', 'update', ['pn_profile', 'pn_hw_tbl']],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    profile = module.params['pn_profile']
    hw_tbl = module.params['pn_hw_tbl']
    enable = module.params['pn_enable']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'vflow-table-profile-modify':
        cli += ' %s ' % command
        if profile:
            cli += ' profile ' + profile
        if hw_tbl:
            cli += ' hw-tbl ' + hw_tbl

        cli += booleanArgs(enable, 'enable', 'disable')

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
