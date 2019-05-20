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
module: pn_vrouter_ospf
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/remove vrouter-ospf
description:
  - This module can be used to add OSPF protocol to vRouter
    and remove OSPF protocol from a vRouter
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - vrouter-ospf configuration command.
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  pn_netmask:
    description:
      - OSPF network IP address netmask.
    required: false
    type: str
  pn_ospf_area:
    description:
      - stub area number for the configuration.
    required: false
    type: str
  pn_network:
    description:
      - OSPF network IP address.
    required: true
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: true
    type: str
"""

EXAMPLES = """
- name: Add OSPF to vRouter
  pn_vrouter_ospf:
    state: 'present'
    pn_vrouter_name: 'sw01-vrouter'
    pn_network: '105.104.104.1'
    pn_netmask: '24'
    pn_ospf_area: '0'
- name: "Remove OSPF to vRouter"
  pn_vrouter_ospf:
    state: 'absent'
    pn_vrouter_name: 'sw01-vrouter'
    pn_network: '105.104.104.1'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-ospf command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-ospf command.
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
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If an OSPF network with the given ip exists on the given vRouter,
    return NETWORK_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :return Booleans: VROUTER_EXISTS, NETWORK_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    network = module.params['pn_network']
    show_cli = pn_cli(module)

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    out = run_commands(module, check_vrouter)[1]
    if out:
        out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    # Check for OSPF networks
    check_network = cli + ' vrouter-ospf-show vrouter-name %s ' % vrouter_name
    check_network += 'format network no-show-headers'
    out = run_commands(module, check_network)[1]

    if out and network in out:
        NETWORK_EXISTS = True
    else:
        NETWORK_EXISTS = False

    return VROUTER_EXISTS, NETWORK_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-ospf-add',
        absent='vrouter-ospf-remove'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_netmask=dict(required=False, type='str'),
        pn_ospf_area=dict(required=False, type='str'),
        pn_network=dict(required=True, type='str'),
        pn_vrouter_name=dict(required=True, type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ['pn_vrouter_name', 'pn_network', 'pn_netmask', 'pn_ospf_area']],
            ["state", "absent", ['pn_vrouter_name', 'pn_network']],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    netmask = module.params['pn_netmask']
    ospf_area = module.params['pn_ospf_area']
    network = module.params['pn_network']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)
    VROUTER_EXISTS, NETWORK_EXISTS = check_cli(module, cli)

    if state:
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )

    if command == 'vrouter-ospf-remove':
        if NETWORK_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='OSPF with network %s dose not exists' % network
            )
    cli += ' %s vrouter-name %s network %s' % (command, vrouter_name, network)

    if command == 'vrouter-ospf-add':
        if NETWORK_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='OSPF with network %s already exists' % network
            )
        if netmask:
            cli += ' netmask ' + netmask
        if ospf_area:
            cli += ' ospf-area ' + ospf_area

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
