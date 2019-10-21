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
module: pn_vrouter_ospf6
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove vrouter-ospf6
description:
  - This module can be used to add interface ip to OSPF6 protocol
    or remove interface ip from OSPF6 protocol on vRouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to add vrouter-ospf6 and
        C(absent) to remove interface from vrouter-ospf6.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_ospf6_area:
    description:
      - area id for this interface in IPv4 address format.
    required: false
    type: str
  pn_nic:
    description:
      - OSPF6 control for this interface.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: false
    type: str
"""

EXAMPLES = """
- name: Add vrouter interface nic to ospf6
  pn_vrouter_ospf6:
    pn_cliswitch: "sw01"
    state: "present"
    pn_vrouter_name: "foo-vrouter"
    pn_nic: "eth0.4092"
    pn_ospf6_area: "0.0.0.0"

- name: Remove vrouter interface nic to ospf6
  pn_vrouter_ospf6:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_vrouter_name: "foo-vrouter"
    pn_nic: "eth0.4092"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-ospf6 command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-ospf6 command.
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
    False. This is required for vrouter-ospf6-remove.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Booleans: VROUTER_EXISTS, NIC_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    nic_str = module.params['pn_nic']

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    out = run_commands(module, check_vrouter)[1]
    if out:
        out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    if nic_str:
        # Check for nic
        show = cli + ' vrouter-ospf6-show vrouter-name %s format nic no-show-headers' % vrouter_name
        out = run_commands(module, show)[1]

        if out:
            out.split()

        NIC_EXISTS = True if nic_str in out else False

    return VROUTER_EXISTS, NIC_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-ospf6-add',
        absent='vrouter-ospf6-remove'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_ospf6_area=dict(required=False, type='str'),
            pn_nic=dict(required=False, type='str'),
            pn_vrouter_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_vrouter_name", "pn_nic",
                                  "pn_ospf6_area"]],
            ["state", "absent", ["pn_vrouter_name", "pn_nic"]]
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    ospf6_area = module.params['pn_ospf6_area']
    nic = module.params['pn_nic']
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

    cli += ' %s vrouter-name %s ' % (command, vrouter_name)

    if command == 'vrouter-ospf6-add':
        if NIC_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='OSPF6 with nic %s already exist' % nic
            )
        if nic:
            cli += ' nic %s' % nic
        if ospf6_area:
            cli += ' ospf6-area %s ' % ospf6_area

    if command == 'vrouter-ospf6-remove':
        if NIC_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='OSPF6 with nic %s does not exist' % nic
            )
        if nic:
            cli += ' nic %s' % nic

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
