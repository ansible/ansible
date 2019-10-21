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
module: pn_ipv6security_raguard_vlan
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/remove ipv6security-raguard-vlan
description:
  - This module can be used to Add vlans to RA Guard Policy and Remove vlans to RA Guard Policy.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - ipv6security-raguard-vlan configuration command.
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  pn_vlans:
    description:
      - Vlans attached to RA Guard Policy.
    required: true
    type: str
  pn_name:
    description:
      - RA Guard Policy Name.
    required: true
    type: str
"""

EXAMPLES = """
- name: ipv6 security raguard vlan add
  pn_ipv6security_raguard_vlan:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_vlans: "100-105"

- name: ipv6 security raguard vlan add
  pn_ipv6security_raguard_vlan:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_vlans: "100"

- name: ipv6 security raguard vlan remove
  pn_ipv6security_raguard_vlan:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_vlans: "100-105"
    state: 'absent'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the ipv6security-raguard-vlan command.
  returned: always
  type: list
stderr:
  description: set of error responses from the ipv6security-raguard-vlan command.
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
    This method checks for idempotency using the ipv6-security-reguard command.
    If a name exists, return True if name exists else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']
    vlans = module.params['pn_vlans']
    show = cli

    cli += ' ipv6security-raguard-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    NAME_EXISTS = True if name in out else False

    show += ' vlan-show format id no-show-headers'
    out = run_commands(module, show)[1]
    if out:
        out = out.split()

    if vlans and '-' in vlans:
        vlan_list = list()
        vlans = vlans.strip().split('-')
        for vlan in range(int(vlans[0]), int(vlans[1]) + 1):
            vlan_list.append(str(vlan))

        for vlan in vlan_list:
            if vlan not in out:
                module.fail_json(
                    failed=True,
                    msg='vlan id %s does not exist. Make sure you create vlan before adding it' % vlan
                )
    else:
        if vlans not in out:
            module.fail_json(
                failed=True,
                msg='vlan id %s does not exist. Make sure you create vlan before adding it' % vlans
            )

    return NAME_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='ipv6security-raguard-vlan-add',
        absent='ipv6security-raguard-vlan-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
            pn_vlans=dict(required=True, type='str'),
            pn_name=dict(required=True, type='str'),
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    vlans = module.params['pn_vlans']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)

    cli += ' %s name %s ' % (command, name)

    if command:
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='ipv6security raguard with name %s does not exist' % name
            )
        if vlans:
            cli += ' vlans ' + vlans

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
