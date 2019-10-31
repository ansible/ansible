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
module: pn_port_cos_bw
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify port-cos-bw
description:
  - This module can be used to update bw settings for CoS queues.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the port-cos-bw.
    required: True
    type: str
    choices: ['update']
  pn_max_bw_limit:
    description:
      - Maximum b/w in percentage.
    required: False
    type: str
  pn_cos:
    description:
      - CoS priority.
    required: False
    type: str
  pn_port:
    description:
      - physical port number.
    required: False
    type: str
  pn_weight:
    description:
      - Scheduling weight (1 to 127) after b/w guarantee met.
    required: False
    type: str
    choices: ['priority', 'no-priority']
  pn_min_bw_guarantee:
    description:
      - Minimum b/w in percentage.
    required: False
    type: str
"""

EXAMPLES = """
- name: port cos bw modify
  pn_port_cos_bw:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "1"
    pn_cos: "0"
    pn_min_bw_guarantee: "60"

- name: port cos bw modify
  pn_port_cos_bw:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "all"
    pn_cos: "0"
    pn_weight: "priority"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the port-cos-bw command.
  returned: always
  type: list
stderr:
  description: set of error responses from the port-cos-bw command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='port-cos-bw-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_max_bw_limit=dict(required=False, type='str'),
            pn_cos=dict(required=False, type='str'),
            pn_port=dict(required=False, type='str'),
            pn_weight=dict(required=False, type='str',
                           choices=['priority', 'no-priority']),
            pn_min_bw_guarantee=dict(required=False, type='str'),
        ),
        required_if=(
            ['state', 'update', ['pn_cos', 'pn_port']],
        ),
        required_one_of=[['pn_max_bw_limit', 'pn_min_bw_guarantee', 'pn_weight']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    max_bw_limit = module.params['pn_max_bw_limit']
    cos = module.params['pn_cos']
    port = module.params['pn_port']
    weight = module.params['pn_weight']
    min_bw_guarantee = module.params['pn_min_bw_guarantee']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'port-cos-bw-modify':
        cli += ' %s ' % command
        if max_bw_limit:
            cli += ' max-bw-limit ' + max_bw_limit
        if cos:
            cli += ' cos ' + cos
        if port:
            cli += ' port ' + port
        if weight:
            cli += ' weight ' + weight
        if min_bw_guarantee:
            cli += ' min-bw-guarantee ' + min_bw_guarantee

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
