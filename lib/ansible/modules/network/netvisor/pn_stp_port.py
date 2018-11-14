#!/usr/bin/python
""" PN CLI stp-port-modify """
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
module: pn_stp_port
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to modify stp-port.
description:
  - C(modify): modify Spanning Tree Protocol (STP) parameters
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
  state:
    description:
      - State the action to perform. Use 'update' to update stp-port.
    required: True
  pn_priority:
    description:
      - STP port priority from 0 to 240 - default 128
    type: str
  pn_cost:
    description:
      - STP port cost from 1 to 200000000 - default 2000
    type: str
  pn_root_guard:
    description:
      - STP port Root guard
  pn_filter:
    description:
      - STP port filters BPDUs
  pn_edge:
    description:
      - STP port is an edge port
  pn_bpdu_guard:
    description:
      - STP port BPDU guard
  pn_port:
    description:
      - STP port
    type: str
  pn_block:
    description:
      - Specify if a STP port blocks BPDUs
"""

EXAMPLES = """
- name: Modify stp port
  pn_stp_port:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "1"
    pn_filter: True

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


import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli
from ansible.module_utils.pn_nvos import booleanArgs


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


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        update='stp-port-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_priority=dict(required=False, type='str'),
            pn_cost=dict(required=False, type='str'),
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
        required_one_of=([['pn_cost', 'pn_root_guard', 'pn_filter',
                           'pn_edge', 'pn_bpdu_guard', 'pn_block']]),
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
        if priority:
            cli += ' priority ' + priority
        if cost:
            cli += ' cost ' + cost
        if port:
            cli += ' port ' + port

        cli += booleanArgs(root_guard, 'root-guard', 'no-root-guard')
        cli += booleanArgs(pn_filter, 'filter', 'no-filter')
        cli += booleanArgs(edge, 'edge', 'no-edge')
        cli += booleanArgs(bpdu_guard, 'bpdu-guard', 'no-bpdu-guard')
        cli += booleanArgs(block, 'block', 'no-block')

    run_cli(module, cli)


if __name__ == '__main__':
    main()
