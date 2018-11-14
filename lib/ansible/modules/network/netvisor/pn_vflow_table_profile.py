#!/usr/bin/python
""" PN CLI vflow-table-profile-modify """

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
module: pn_vflow_table_profile
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to modify vflow-table-profile.
description:
  - C(modify): modify a vFlow table profile
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'update' to modify
        the vflow-table-profile.
    required: True
  pn_profile:
    description:
      - type of vFlow profile
    required: false
    choices: ['application', 'ipv6', 'qos']
  pn_hw_tbl:
    description:
      - hardware table used by vFlow
    required: false
    choices: ['switch-main', 'switch-hash', 'npu-main', 'npu-hash']
  pn_enable:
    description:
      - enable or disable vflow profile table
    required: false
    type: bool
"""

EXAMPLES = """
- name: Modify vflow table profile
  pn_vflow_table_profile:
    state: 'update'
    pn_profile: 'ipv6'
    pn_hw_tbl: 'switch-main'
    pn_enable: True

- name: Modify vflow table profile
  pn_vflow_table_profile:
    state: 'update'
    pn_profile: 'qos'
    pn_hw_tbl: 'switch-main'
    pn_enable: False
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the vflow-table-profile command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vflow-table-profile command.
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


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        update='vflow-table-profile-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_profile=dict(required=False, type='str',
                            choices=['application', 'ipv6', 'qos']),
            pn_hw_tbl=dict(required=False, type='str',
                           choices=['switch-main', 'switch-hash',
                                    'npu-main', 'npu-hash']),
            pn_enable=dict(required=False, type='bool'),
        ),
        required_if=(
            ['state', 'update', ['pn_profile', 'pn_hw_tbl']],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    profile = module.params['pn_profile']
    hw_tbl = module.params['pn_hw_tbl']
    enable = module.params['pn_enable']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'vflow-table-profile-modify':
        cli += ' %s ' % command
        if profile:
            cli += ' profile ' + profile
        if hw_tbl:
            cli += ' hw-tbl ' + hw_tbl
        if enable:
            cli += ' enable '
        else:
            cli += ' no-enable '

    run_cli(module, cli)


if __name__ == '__main__':
    main()
