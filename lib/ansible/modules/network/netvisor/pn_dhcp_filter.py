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
module: pn_dhcp_filter
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete dhcp-filter
description:
  - This module can be used to create, delete and modify a DHCP filter config.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create dhcp-filter and
        C(absent) to delete dhcp-filter C(update) to modify the dhcp-filter.
    required: True
    type: str
    choices: ['present', 'absent', 'update']
  pn_trusted_ports:
    description:
      - trusted ports of dhcp config.
    required: False
    type: str
  pn_name:
    description:
      - name of the DHCP filter.
    required: false
    type: str
"""

EXAMPLES = """
- name: dhcp filter create
  pn_dhcp_filter:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    state: "present"
    pn_trusted_ports: "1"

- name: dhcp filter delete
  pn_dhcp_filter:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    state: "absent"
    pn_trusted_ports: "1"

- name: dhcp filter modify
  pn_dhcp_filter:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    state: "update"
    pn_trusted_ports: "1,2"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the dhcp-filter command.
  returned: always
  type: list
stderr:
  description: set of error responses from the dhcp-filter command.
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
    This method checks for idempotency using the dhcp-filter-show command.
    If a user with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    user_name = module.params['pn_name']

    cli += ' dhcp-filter-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if user_name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='dhcp-filter-create',
        absent='dhcp-filter-delete',
        update='dhcp-filter-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_trusted_ports=dict(required=False, type='str'),
            pn_name=dict(required=False, type='str'),
        ),
        required_if=[
            ["state", "present", ["pn_name", "pn_trusted_ports"]],
            ["state", "absent", ["pn_name"]],
            ["state", "update", ["pn_name", "pn_trusted_ports"]]
        ]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    trusted_ports = module.params['pn_trusted_ports']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    USER_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'dhcp-filter-modify':
        if USER_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='dhcp-filter with name %s does not exist' % name
            )
    if command == 'dhcp-filter-delete':
        if USER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='dhcp-filter with name %s does not exist' % name
            )
    if command == 'dhcp-filter-create':
        if USER_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='dhcp-filter with name %s already exists' % name
            )
    if command != 'dhcp-filter-delete':
        if trusted_ports:
            cli += ' trusted-ports ' + trusted_ports

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
