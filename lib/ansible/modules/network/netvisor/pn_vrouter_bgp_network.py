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
module: pn_vrouter_bgp_network
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove vrouter-bgp-network
description:
  - This module can be used to add Border Gateway Protocol network to a vRouter
    and remove Border Gateway Protocol network from a vRouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to add bgp network and
        C(absent) to remove bgp network.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_netmask:
    description:
      - BGP network mask.
    required: false
    type: str
  pn_network:
    description:
      - IP address for BGP network.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: false
    type: str
"""

EXAMPLES = """
- name:  Add network to bgp
  pn_vrouter_bgp_network:
    pn_cliswitch: "sw01"
    state: "present"
    pn_vrouter_name: "foo-vrouter"
    pn_network: '10.10.10.10'
    pn_netmask: '31'

- name:  Remove network from bgp
  pn_vrouter_bgp_network:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_vrouter_name: "foo-vrouter"
    pn_network: '10.10.10.10'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-bgp-network command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-bgp-network command.
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
    This method checks for pim ssm config using the vrouter-show command.
    If a user already exists on the given switch, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_vrouter_name']
    network = module.params['pn_network']

    show = cli
    cli += ' vrouter-show name %s format name no-show-headers' % name
    rc, out, err = run_commands(module, cli)
    VROUTER_EXISTS = '' if out else None

    cli = show
    cli += ' vrouter-bgp-network-show vrouter-name %s network %s format network no-show-headers' % (name, network)
    out = run_commands(module, cli)[1]
    out = out.split()
    NETWORK_EXISTS = True if network in out[-1] else False

    return NETWORK_EXISTS, VROUTER_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-bgp-network-add',
        absent='vrouter-bgp-network-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_netmask=dict(required=False, type='str'),
            pn_network=dict(required=False, type='str'),
            pn_vrouter_name=dict(required=False, type='str'),
        ),
        required_if=(
            ['state', 'present', ['pn_vrouter_name', 'pn_netmask', 'pn_network']],
            ['state', 'absent', ['pn_vrouter_name', 'pn_network']],
        ),
    )

    # Accessing the arguments
    state = module.params['state']
    cliswitch = module.params['pn_cliswitch']
    netmask = module.params['pn_netmask']
    network = module.params['pn_network']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NETWORK_EXISTS, VROUTER_EXISTS = check_cli(module, cli)

    if VROUTER_EXISTS is None:
        module.fail_json(
            failed=True,
            msg='vRouter %s does not exists' % vrouter_name
        )

    if command == 'vrouter-bgp-network-add':
        if NETWORK_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Network %s already added to bgp' % network
            )

    if command == 'vrouter-bgp-network-remove':
        if NETWORK_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Network %s does not exists' % network
            )

    cli += ' %s vrouter-name %s ' % (command, vrouter_name)

    if netmask:
        cli += ' netmask ' + netmask
    if network:
        cli += ' network ' + network

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
