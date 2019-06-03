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
module: pn_vrouter_packet_relay
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/remove vrouter-packet-relay
description:
  - This module can be used to add packet relay configuration for DHCP on vrouter
    and remove packet relay configuration for DHCP on vrouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - vrouter-packet-relay configuration command.
    required: false
    choices: ['present', 'absent']
    type: str
    default: 'present'
  pn_forward_ip:
    description:
      - forwarding IP address.
    required: true
    type: str
  pn_nic:
    description:
      - NIC.
    required: true
    type: str
  pn_forward_proto:
    description:
      - protocol type to forward packets.
    required: false
    type: str
    choices: ['dhcp']
    default: 'dhcp'
  pn_vrouter_name:
    description:
      - name of service config.
    required: true
    type: str
"""

EXAMPLES = """
- name: vRouter packet relay add
  pn_vrouter_packet_relay:
    pn_cliswitch: "sw01"
    pn_forward_ip: "192.168.10.1"
    pn_nic: "eth0.4092"
    pn_vrouter_name: "sw01-vrouter"

- name: vRouter packet relay remove
  pn_vrouter_packet_relay:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_forward_ip: "192.168.10.1"
    pn_nic: "eth0.4092"
    pn_vrouter_name: "sw01-vrouter"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-packet-relay command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-packet-relay command.
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

    If nic_str exists on the given vRouter, return NIC_EXISTS as True else
    False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Booleans: VROUTER_EXISTS, NIC_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    nic_str = module.params['pn_nic']

    # Check for vRouter
    check_vrouter = 'vrouter-show format name no-show-headers'
    out = run_commands(module, check_vrouter)[1]

    if out:
        out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    if nic_str:
        # Check for nic
        show = 'vrouter-interface-show vrouter-name %s format nic no-show-headers' % vrouter_name
        out = run_commands(module, show)[1]
        if out:
            out = out.split()

        NIC_EXISTS = True if nic_str in out else False

    return VROUTER_EXISTS, NIC_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-packet-relay-add',
        absent='vrouter-packet-relay-remove'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_forward_ip=dict(required=True, type='str'),
        pn_nic=dict(required=True, type='str'),
        pn_forward_proto=dict(required=False, type='str', choices=['dhcp'], default='dhcp'),
        pn_vrouter_name=dict(required=True, type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ["pn_vrouter_name", "pn_forward_ip", "pn_nic", "pn_forward_proto"]],
            ["state", "absent", ["pn_vrouter_name", "pn_forward_ip", "pn_nic", "pn_forward_proto"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    forward_ip = module.params['pn_forward_ip']
    nic = module.params['pn_nic']
    forward_proto = module.params['pn_forward_proto']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    VROUTER_EXISTS, NIC_EXISTS = check_cli(module, cli)

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

    if command == 'vrouter-packet-relay-add' or command == 'vrouter-packet-relay-remove':
        cli += ' %s' % command
        cli += ' vrouter-name %s nic %s' % (vrouter_name, nic)
        cli += ' forward-proto %s forward-ip %s' % (forward_proto, forward_ip)

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
