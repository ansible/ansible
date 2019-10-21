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
module: pn_cpu_class
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete cpu-class
description:
  - This module can be used to create, modify and delete CPU class information.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create cpu-class and
        C(absent) to delete cpu-class C(update) to modify the cpu-class.
    required: True
    type: str
    choices: ['present', 'absent', 'update']
  pn_scope:
    description:
      - scope for CPU class.
    required: false
    choices: ['local', 'fabric']
  pn_hog_protect:
    description:
      - enable host-based hog protection.
    required: False
    type: str
    choices: ['disable', 'enable', 'enable-and-drop']
  pn_rate_limit:
    description:
      - rate-limit for CPU class.
    required: False
    type: str
  pn_name:
    description:
      - name for the CPU class.
    required: False
    type: str
"""

EXAMPLES = """
- name: create cpu class
  pn_cpu_class:
    pn_cliswitch: 'sw01'
    state: 'present'
    pn_name: 'icmp'
    pn_rate_limit: '1000'
    pn_scope: 'local'

- name: delete cpu class
  pn_cpu_class:
    pn_cliswitch: 'sw01'
    state: 'absent'
    pn_name: 'icmp'


- name: modify cpu class
  pn_cpu_class:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_name: 'icmp'
    pn_rate_limit: '2000'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the cpu-class command.
  returned: always
  type: list
stderr:
  description: set of error responses from the cpu-class command.
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
    This method checks for idempotency using the cpu-class-show command.
    If a user with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']
    clicopy = cli

    cli += ' system-settings-show format cpu-class-enable no-show-headers'
    out = run_commands(module, cli)[1]
    out = out.split()

    if 'on' not in out:
        module.fail_json(
            failed=True,
            msg='Enable CPU class before creating or deleting'
        )

    cli = clicopy
    cli += ' cpu-class-show format name no-show-headers'
    out = run_commands(module, cli)[1]
    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='cpu-class-create',
        absent='cpu-class-delete',
        update='cpu-class-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_hog_protect=dict(required=False, type='str',
                                choices=['disable', 'enable',
                                         'enable-and-drop']),
            pn_rate_limit=dict(required=False, type='str'),
            pn_name=dict(required=False, type='str'),
        ),
        required_if=(
            ['state', 'present', ['pn_name', 'pn_scope', 'pn_rate_limit']],
            ['state', 'absent', ['pn_name']],
            ['state', 'update', ['pn_name']],
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    scope = module.params['pn_scope']
    hog_protect = module.params['pn_hog_protect']
    rate_limit = module.params['pn_rate_limit']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'cpu-class-modify':
        if NAME_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='cpu class with name %s does not exist' % name
            )

    if command == 'cpu-class-delete':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='cpu class with name %s does not exist' % name
            )

    if command == 'cpu-class-create':
        if NAME_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='cpu class with name %s already exists' % name
            )
        if scope:
            cli += ' scope %s ' % scope

    if command != 'cpu-class-delete':
        if hog_protect:
            cli += ' hog-protect %s ' % hog_protect
        if rate_limit:
            cli += ' rate-limit %s ' % rate_limit

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
