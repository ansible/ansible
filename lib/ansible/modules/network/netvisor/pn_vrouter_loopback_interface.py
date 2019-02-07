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
module: pn_vrouter_loopback_interface
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove vrouter-loopback-interface
description:
  - This module can be used to add loopback interface to a vRouter or
    remove loopback interface from a vRouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to add vrouter-loopback-interface
        and C(absent) to remove vrouter-loopback-interface.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_ip:
    description:
      - loopback IP address.
    required: false
    type: str
  pn_index:
    description:
      - loopback index from 1 to 255.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: false
    type: str
"""

EXAMPLES = """
- name: Add vrouter loopback interface
  pn_vrouter_loopback_interface:
    state: "present"
    pn_cliswitch: "sw01"
    pn_vrouter_name: "sw01-vrouter"
    pn_ip: "192.168.10.1"

- name: Remove vrouter loopback interface
  pn_vrouter_loopback_interface:
    state: "absent"
    pn_cliswitch: "sw01"
    pn_vrouter_name: "sw01-vrouter"
    pn_ip: "192.168.10.1"
    pn_index: "2"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-loopback-interface command.
  returned: always
  type: list
stderr:
  description: set of error response from the vrouter-loopback-interface
               command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli


def check_cli(module, cli):
    """
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the vrouter-interface-show
    command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Booleans: VROUTER_EXISTS, INTERFACE_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_ip']

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    out = module.run_command(check_vrouter, use_unsafe_shell=True)[1]
    out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    if interface_ip:
        # Check for interface and VRRP and fetch nic for VRRP
        show = cli + ' vrouter-loopback-interface-show vrouter-name %s ip %s format ip no-show-headers' % (vrouter_name, interface_ip)
        out = module.run_command(show, use_unsafe_shell=True)[1]

        if out and interface_ip in out.split(' ')[1]:
            INTERFACE_EXISTS = True
        else:
            INTERFACE_EXISTS = False

    return VROUTER_EXISTS, INTERFACE_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-loopback-interface-add',
        absent='vrouter-loopback-interface-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_ip=dict(required=False, type='str'),
            pn_index=dict(required=False, type='str'),
            pn_vrouter_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_vrouter_name", "pn_ip"]],
            ["state", "absent", ["pn_vrouter_name", "pn_ip", "pn_index"]]
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    ip = module.params['pn_ip']
    index = module.params['pn_index']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    VROUTER_EXISTS, INTERFACE_EXISTS = check_cli(module, cli)

    if VROUTER_EXISTS is False:
        module.fail_json(
            failed=True,
            msg='vRouter %s does not exist' % vrouter_name
        )

    cli += ' %s vrouter-name %s ' % (command, vrouter_name)

    if index and (int(index) < 1 or int(index) > 255):
        module.fail_json(
            failed=True,
            msg='index should be in range 1 to 255'
        )

    if command == 'vrouter-loopback-interface-add':
        if INTERFACE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='vRouter with loopback ip %s exist' % ip
            )
        if ip:
            cli += ' ip ' + ip
        if index:
            cli += ' index ' + index

    if command == 'vrouter-loopback-interface-remove':
        if INTERFACE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter with loopback ip %s does not exist' % ip
            )

        if index:
            cli += ' index ' + index

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
