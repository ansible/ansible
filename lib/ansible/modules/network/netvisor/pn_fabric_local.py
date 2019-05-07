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
module: pn_fabric_local
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to modify fabric-local
description:
  - This module can be used to modify fabric local information.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: true
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the fabric-local.
    required: false
    type: str
    choices: ['update']
    default: 'update'
  pn_fabric_network:
    description:
      - fabric administration network.
    required: false
    choices: ['in-band', 'mgmt', 'vmgmt']
    default: 'mgmt'
  pn_vlan:
    description:
      - VLAN assigned to fabric.
    required: false
    type: str
  pn_control_network:
    description:
      - control plane network.
    required: false
    choices: ['in-band', 'mgmt', 'vmgmt']
  pn_fabric_advertisement_network:
    description:
      - network to send fabric advertisements on.
    required: false
    choices: ['inband-mgmt', 'inband-only', 'inband-vmgmt', 'mgmt-only']
"""

EXAMPLES = """
- name: Fabric local module
  pn_fabric_local:
    pn_cliswitch: "sw01"
    pn_vlan: "500"

- name: Fabric local module
  pn_fabric_local:
    pn_cliswitch: "sw01"
    pn_fabric_advertisement_network: "mgmt-only"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the fabric-local command.
  returned: always
  type: list
stderr:
  description: set of error responses from the fabric-local command.
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


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='fabric-local-modify'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=True, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='update'),
        pn_fabric_network=dict(required=False, type='str',
                               choices=['mgmt', 'in-band', 'vmgmt'], default='mgmt'),
        pn_vlan=dict(required=False, type='str'),
        pn_control_network=dict(required=False, type='str',
                                choices=['in-band', 'mgmt', 'vmgmt']),
        pn_fabric_advertisement_network=dict(required=False, type='str',
                                             choices=['inband-mgmt', 'inband-only', 'inband-vmgmt', 'mgmt-only']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['pn_fabric_network', 'pn_vlan',
                          'pn_control_network',
                          'pn_fabric_advertisement_network']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    fabric_network = module.params['pn_fabric_network']
    vlan = module.params['pn_vlan']
    control_network = module.params['pn_control_network']
    fabric_adv_network = module.params['pn_fabric_advertisement_network']

    command = state_map[state]

    if vlan:
        if int(vlan) < 1 or int(vlan) > 4092:
            module.fail_json(
                failed=True,
                msg='Valid vlan range is 1 to 4092'
            )
        cli = pn_cli(module, cliswitch)
        cli += ' vlan-show format id no-show-headers'
        out = run_commands(module, cli)[1].split()

        if vlan in out and vlan != '1':
            module.fail_json(
                failed=True,
                msg='vlan %s is already in used. Specify unused vlan' % vlan
            )

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'fabric-local-modify':
        cli += ' %s ' % command

        if fabric_network:
            cli += ' fabric-network ' + fabric_network

        if vlan:
            cli += ' vlan ' + vlan

        if control_network:
            cli += ' control-network ' + control_network

        if fabric_adv_network:
            cli += ' fabric-advertisement-network ' + fabric_adv_network

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
