#!/usr/bin/python
""" PN CLI cpu-class-create/modify/delete """

# Copyright 2018 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_cpu_class
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/modify/delete cpu-class.
description:
  - C(create): Add CPU class
  - C(modify): modify CPU class information
  - C(delete): delete a CPU class
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to create cpu-class and
        'absent' to delete cpu-class 'update' to modify the cpu-class.
    required: True
  pn_scope:
    description:
      - scope for CPU class
    required: false
    choices: ['local', 'fabric']
  pn_hog_protect:
    description:
      - enable host-based hog protection
    required: false
    choices: ['disable', 'enable', 'enable-and-drop']
  pn_rate_limit:
    description:
      - rate-limit for CPU class
    required: false
    type: str
  pn_name:
    description:
      - name for the CPU class
    required: false
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
    pn_name: 'ospf'
    pn_rate_limit: '1000'
    pn_hog_protect: 'enable'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
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

import shlex
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    state = module.params['state']
    command = state_map[state]

    cmd = shlex.split(cli)
    result, out, err = module.run_command(cmd)

    remove_cmd = '/usr/bin/cli --quiet -e --no-login-prompt'

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            msg="%s operation completed" % command,
            changed=True
        )


def check_cli(module, cli):
    """
    This method checks for idempotency using the cpu-class-show command.
    If a user with given name exists, return NAME_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: NAME_EXISTS
    """
    # Global flags
    global NAME_EXISTS

    name = module.params['pn_name']

    show = cli + \
        ' cpu-class-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()

    NAME_EXISTS = True if name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
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

    check_cli(module, cli)
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

    run_cli(module, cli)


if __name__ == '__main__':
    main()
