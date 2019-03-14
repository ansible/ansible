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
module: pn_vrouter_interface_ip
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove vrouter-interface-ip
description:
  - This module can be used to add an IP address on interface from a vRouter
    or remove an IP address on interface from a vRouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to addvrouter-interface-ip
        and C(absent) to remove vrouter-interface-ip.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_bd:
    description:
      - interface Bridge Domain.
    required: false
    type: str
  pn_netmask:
    description:
      - netmask.
    required: false
    type: str
  pn_vnet:
    description:
      - interface VLAN VNET.
    required: false
    type: str
  pn_ip:
    description:
      - IP address.
    required: false
    type: str
  pn_nic:
    description:
      - virtual NIC assigned to interface.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: false
    type: str
"""

EXAMPLES = """
- name: Add vrouter interface to nic
  pn_vrouter_interface_ip:
    state: "present"
    pn_cliswitch: "sw01"
    pn_vrouter_name: "foo-vrouter"
    pn_ip: "2620:0:1651:1::30"
    pn_netmask: "127"
    pn_nic: "eth0.4092"

- name: Remove vrouter interface to nic
  pn_vrouter_interface_ip:
    state: "absent"
    pn_cliswitch: "sw01"
    pn_vrouter_name: "foo-vrouter"
    pn_ip: "2620:0:1651:1::30"
    pn_nic: "eth0.4092"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-interface-ip command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-interface-ip command.
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
    This method also checks for idempotency using the vrouter-interface-show
    command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.

    If an interface with the given ip exists on the given vRouter,
    return INTERFACE_EXISTS as True else False. This is required for
    vrouter-interface-add.

    If nic_str exists on the given vRouter, return NIC_EXISTS as True else
    False. This is required for vrouter-interface-remove.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Booleans: VROUTER_EXISTS, INTERFACE_EXISTS, NIC_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_ip']
    nic_str = module.params['pn_nic']

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show name %s format name no-show-headers ' % vrouter_name
    out = run_commands(module, check_vrouter)[1]
    out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out[-1] else False

    if interface_ip:
        # Check for interface and VRRP and fetch nic for VRRP
        show = cli + ' vrouter-interface-show vrouter-name %s ' % vrouter_name
        show += 'ip2 %s format ip2,nic no-show-headers' % interface_ip
        out = run_commands(module, show)[1]

        if out and interface_ip in out.split(' ')[-2]:
            INTERFACE_EXISTS = True
        else:
            INTERFACE_EXISTS = False

    if nic_str:
        # Check for nic
        show = cli + ' vrouter-interface-show vrouter-name %s ' % vrouter_name
        show += ' format nic no-show-headers'
        out = run_commands(module, show)[1]
        out = out.split()

        NIC_EXISTS = True if nic_str in out else False

    return VROUTER_EXISTS, INTERFACE_EXISTS, NIC_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-interface-ip-add',
        absent='vrouter-interface-ip-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_bd=dict(required=False, type='str'),
            pn_netmask=dict(required=False, type='str'),
            pn_vnet=dict(required=False, type='str'),
            pn_ip=dict(required=False, type='str'),
            pn_nic=dict(required=False, type='str'),
            pn_vrouter_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_vrouter_name", "pn_nic", "pn_ip", "pn_netmask"]],
            ["state", "absent", ["pn_vrouter_name", "pn_nic", "pn_ip"]]
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    bd = module.params['pn_bd']
    netmask = module.params['pn_netmask']
    vnet = module.params['pn_vnet']
    ip = module.params['pn_ip']
    nic = module.params['pn_nic']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    VROUTER_EXISTS, INTERFACE_EXISTS, NIC_EXISTS = check_cli(module, cli)

    if VROUTER_EXISTS is False:
        module.fail_json(
            failed=True,
            msg='vRouter %s does not exist' % vrouter_name
        )

    if NIC_EXISTS is False:
        module.fail_json(
            failed=True,
            msg='vRouter with nic %s does not exist' % nic
        )

    cli += ' %s vrouter-name %s ' % (command, vrouter_name)

    if command == 'vrouter-interface-ip-add':
        if INTERFACE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='vRouter with interface %s exist' % ip
            )
        cli += ' nic %s ip %s ' % (nic, ip)

        if bd:
            cli += ' bd ' + bd
        if netmask:
            cli += ' netmask ' + netmask
        if vnet:
            cli += ' vnet ' + vnet

    if command == 'vrouter-interface-ip-remove':
        if INTERFACE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter with interface %s does not exist' % ip
            )
        if nic:
            cli += ' nic %s ' % nic
        if ip:
            cli += ' ip %s ' % ip.split('/')[0]

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
