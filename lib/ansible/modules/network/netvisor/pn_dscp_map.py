#!/usr/bin/python
""" PN CLI dscp-map-create/delete """

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
module: pn_dscp_map
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/delete dscp-map.
description:
  - C(create): Create a DSCP priority mapping table
  - C(delete): Delete a DSCP priority mapping table
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to create dscp-map and
        'absent' to delete.
    required: True
  pn_name:
    description:
      - Name for the DSCP map
    required: false
    type: str
  pn_scope:
    description:
      - scope for dscp map
    required: false
    choices: ['local', 'fabric']
"""

EXAMPLES = """
- name: dscp map create
  pn_dscp_map:
    pn_cliswitch: "sw01"
    state: "present"
    pn_name: "foo"
    pn_scope: "local"

- name: dscp map delete
  pn_dscp_map:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_name: "foo"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the dscp-map command.
  returned: always
  type: list
stderr:
  description: set of error responses from the dscp-map command.
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
    This method checks for idempotency using the dscp-map-show name command.
    If a user with given name exists, return NAME_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: NAME_EXISTS
    """
    # Global flags
    global NAME_EXISTS
    name = module.params['pn_name']

    show = cli + \
        ' dscp-map-show name %s format name no-show-headers' % name
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()

    NAME_EXISTS = True if name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        present='dscp-map-create',
        absent='dscp-map-delete'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_name=dict(required=False, type='str'),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_scope"]],
            ["state", "absent", ["pn_name"]],
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    name = module.params['pn_name']
    scope = module.params['pn_scope']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'dscp-map-delete':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='dscp map with name %s does not exist' % name
            )
    else:
        if command == 'dscp-map-create':
            if NAME_EXISTS is True:
                module.exit_json(
                     skipped=True,
                     msg='dscp map with name %s already exists' % name
                )

        if scope:
            cli += ' scope ' + scope

    run_cli(module, cli)


if __name__ == '__main__':
    main()
