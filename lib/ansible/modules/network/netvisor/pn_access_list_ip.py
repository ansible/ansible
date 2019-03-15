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
module: pn_access_list_ip
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to add/remove access-list-ip
description:
  - This modules can be used to add and remove IPs associated with access list.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to add access-list-ip and
        'absent' to remove access-list-ip.
    required: True
    choices: ["present", "absent"]
  pn_ip:
    description:
      - IP associated with the access list.
    required: False
    default: '::'
    type: str
  pn_name:
    description:
      - Access List Name.
    required: False
    type: str
"""

EXAMPLES = """
- name: access list ip functionality
  pn_access_list_ip:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_ip: "172.16.3.1"
    state: "present"

- name: access list ip functionality
  pn_access_list_ip:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_ip: "172.16.3.1"
    state: "absent"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the access-list-ip command.
  returned: always
  type: list
stderr:
  description: set of error responses from the access-list-ip command.
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
    This method checks for idempotency using the access-list-ip-show command.
    If ip  exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']
    ip = module.params['pn_ip']
    clicopy = cli

    cli += ' access-list-show name %s no-show-headers ' % name
    out = run_commands(module, cli)[1]

    if name not in out:
        module.fail_json(
            failed=True,
            msg='access-list with name %s does not exist' % name
        )

    cli = clicopy
    cli += ' access-list-ip-show name %s format ip no-show-headers' % name

    out = run_commands(module, cli)[1]
    out = out.split()
    return True if ip in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='access-list-ip-add',
        absent='access-list-ip-remove',
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_ip=dict(required=False, type='str', default='::'),
            pn_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_name"]],
            ["state", "absent", ["pn_name", "pn_ip"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    ip = module.params['pn_ip']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    IP_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'access-list-ip-remove':
        if IP_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='access-list with ip %s does not exist' % ip
            )
        if ip:
            cli += ' ip ' + ip
    else:
        if command == 'access-list-ip-add':
            if IP_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='access list with ip %s already exists' % ip
                )
        if ip:
            cli += ' ip ' + ip

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
