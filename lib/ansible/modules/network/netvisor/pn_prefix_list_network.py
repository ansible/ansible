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
module: pn_prefix_list_network
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove prefix-list-network
description:
  - This module is used to add network associated with prefix list
    and remove networks associated with prefix list.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create
        prefix-list-network and C(absent) to delete prefix-list-network.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_netmask:
    description:
      - netmask of the network associated the prefix list.
    required: false
    type: str
  pn_name:
    description:
      - Prefix List Name.
    required: false
    type: str
  pn_network:
    description:
      - network associated with the prefix list.
    required: false
    type: str
"""

EXAMPLES = """
- name: prefix list network add
  pn_prefix_list_network:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_network: "172.16.3.1"
    pn_netmask: "24"
    state: "present"

- name: prefix list network remove
  pn_prefix_list_network:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_name: "foo"
    pn_network: "172.16.3.1"
    pn_netmask: "24"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the prefix-list-network command.
  returned: always
  type: list
stderr:
  description: set of error responses from the prefix-list-network command.
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
    This method checks for idempotency using prefix-list-network-show command.
    If network exists, return as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']
    network = module.params['pn_network']
    show = cli

    cli += ' prefix-list-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if name not in out.split()[-1]:
        module.fail_json(
            failed=True,
            msg='Prefix list with name %s does not exists' % name
        )

    cli = show
    cli += ' prefix-list-network-show name %s format network no-show-headers' % name
    rc, out, err = run_commands(module, cli)

    if out:
        out = out.split()[1]
        return True if network in out.split('/')[0] else False

    return False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='prefix-list-network-add',
        absent='prefix-list-network-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_netmask=dict(required=False, type='str'),
            pn_name=dict(required=False, type='str'),
            pn_network=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_network", "pn_netmask"]],
            ["state", "absent", ["pn_name", "pn_network", "pn_netmask"]],
        ),
        required_together=(
            ["pn_network", "pn_netmask"],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    netmask = module.params['pn_netmask']
    name = module.params['pn_name']
    network = module.params['pn_network']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NETWORK_EXISTS = check_cli(module, cli)
    cli += ' %s ' % command

    if command == 'prefix-list-network-remove':
        if NETWORK_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Prefix list with network %s does not exist' % network
            )

    if command == 'prefix-list-network-add':
        if NETWORK_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Prefix list with network %s already exists' % network
            )

    if name:
        cli += ' name ' + name
    if network:
        cli += ' network ' + network
    if netmask:
        cli += ' netmask ' + netmask

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
