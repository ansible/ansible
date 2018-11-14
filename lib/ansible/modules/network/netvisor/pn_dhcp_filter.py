#!/usr/bin/python
""" PN CLI dhcp-filter-create/modify/delete """

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
module: pn_dhcp_filter
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/modify/delete dhcp-filter.
description:
  - C(create): creates a new DHCP filter config
  - C(modify): modify a DHCP filter config
  - C(delete): deletes a DHCP filter config
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to create dhcp-filter and
        'absent' to delete dhcp-filter 'update' to modify the dhcp-filter.
    required: True
  pn_trusted_ports:
    description:
      - trusted ports
    required: false
    type: str
  pn_name:
    description:
      - name of the DHCP filter
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
    This method checks for idempotency using the dhcp-filter-show command.
    If a user with given name exists, return USER_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: USER_EXISTS
    """
    user_name = module.params['pn_name']

    show = cli + \
        ' dhcp-filter-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global USER_EXISTS

    USER_EXISTS = True if user_name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
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

    check_cli(module, cli)
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
                 msg='dhcp-filterwith name %s already exists' % name
            )

    if command != 'dhcp-filter-delete':
        if trusted_ports:
            cli += ' trusted-ports ' + trusted_ports

    run_cli(module, cli)


if __name__ == '__main__':
    main()
