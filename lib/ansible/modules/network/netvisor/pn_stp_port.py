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
module: pn_stp_port
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify stp-port.
description:
  - This module can be used modify Spanning Tree Protocol (STP) parameters on ports.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    type: str
    required: false
  state:
    description:
      - State the action to perform. Use C(update) to update stp-port.
    type: str
    required: true
    choices: ['update']
  pn_priority:
    description:
      - STP port priority from 0 to 240.
    type: str
    default: '128'
  pn_cost:
    description:
      - STP port cost from 1 to 200000000.
    type: str
    default: '2000'
  pn_root_guard:
    description:
      - STP port Root guard.
    type: bool
  pn_filter:
    description:
      - STP port filters BPDUs.
    type: bool
  pn_edge:
    description:
      - STP port is an edge port.
    type: bool
  pn_bpdu_guard:
    description:
      - STP port BPDU guard.
    type: bool
  pn_port:
    description:
      - STP port.
    type: str
  pn_block:
    description:
      - Specify if a STP port blocks BPDUs.
    type: bool
"""

EXAMPLES = """
- name: Modify stp port
  pn_stp_port:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "1"
    pn_filter: True
    pn_priority: '144'

- name: Modify stp port
  pn_stp_port:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "1"
    pn_cost: "200"

- name: Modify stp port
  pn_stp_port:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "1"
    pn_edge: True
    pn_cost: "200"

"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the stp-port command.
  returned: always
  type: list
stderr:
  description: set of error responses from the stp-port command.
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
        update='stp-port-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_priority=dict(required=False, type='str', default='128'),
            pn_cost=dict(required=False, type='str', default='2000'),
            pn_root_guard=dict(required=False, type='bool'),
            pn_filter=dict(required=False, type='bool'),
            pn_edge=dict(required=False, type='bool'),
            pn_bpdu_guard=dict(required=False, type='bool'),
            pn_port=dict(required=False, type='str'),
            pn_block=dict(required=False, type='bool'),
        ),
        required_if=(
            ["state", "update", ["pn_port"]],
        ),
        required_one_of=(
            ['pn_cost', 'pn_root_guard', 'pn_filter',
             'pn_edge', 'pn_bpdu_guard', 'pn_block'],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    priority = module.params['pn_priority']
    cost = module.params['pn_cost']
    root_guard = module.params['pn_root_guard']
    pn_filter = module.params['pn_filter']
    edge = module.params['pn_edge']
    bpdu_guard = module.params['pn_bpdu_guard']
    port = module.params['pn_port']
    block = module.params['pn_block']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'stp-port-modify':
        cli += ' %s ' % command
        if priority and (int(priority) % 16 == 0 and int(priority) < 240):
            cli += ' priority ' + priority
        else:
            module.fail_json(
                failed=True,
                msg='Priority must be increment of 16 and should be less that 240'
            )
        if cost and (int(cost) < 200000000):
            cli += ' cost ' + cost
        else:
            module.fail_json(
                failed=True,
                msg='cost must be between 1 and 200000000'
            )
        if port:
            cli += ' port ' + port

        cli += booleanArgs(root_guard, 'root-guard', 'no-root-guard')
        cli += booleanArgs(pn_filter, 'filter', 'no-filter')
        cli += booleanArgs(edge, 'edge', 'no-edge')
        cli += booleanArgs(bpdu_guard, 'bpdu-guard', 'no-bpdu-guard')
        cli += booleanArgs(block, 'block', 'no-block')

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
