#!/usr/bin/python
""" PN CLI admin-syslog-create/modify/delete """

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
module: pn_admin_syslog
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/modify/delete admin-syslog.
description:
  - C(create): create the scope and other parameters of syslog event collection
  - C(modify): modify parameters of syslog event collection
  - C(delete): delete the scope and other parameters of syslog event collection
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'present' to create admin-syslog and
        'absent' to delete admin-syslog 'update' to modify the admin-syslog.
    required: True
  pn_scope:
    description:
      - scope of the system log
    required: false
    choices: ['local', 'fabric']
  pn_host:
    description:
      - host name to log system events
    required: false
    type: str
  pn_port:
    description:
      - host port
    required: false
    type: str
  pn_transport:
    description:
      - transport for log events - tcp/tls or udp
    required: false
    choices: ['tcp-tls', 'udp']
  pn_message_format:
    description:
      - message-format for log events - structured or legacy
    required: false
    choices: ['structured', 'legacy']
  pn_name:
    description:
      - name of the system log
    required: false
    type: str
"""

EXAMPLES = """
- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: sw01
    state: "absent"
    pn_name: "foo"
    pn_scope: "local"

- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: sw01
    state: "present"
    pn_name: "foo"
    pn_scope: "local"
    pn_host: "166.68.224.46"
    pn_message_format: "structured"

- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: sw01
    state: "update"
    pn_name: "foo"
    pn_scope: "fabric"
    pn_host: "166.68.224.10"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the admin-syslog command.
  returned: always
  type: list
stderr:
  description: set of error responses from the admin-syslog command.
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
    This method checks for idempotency using the admin-syslog-show command.
    If a user with given name exists, return SYSLOG_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: SYSLOG_EXISTS
    """
    # Global flags
    global SYSLOG_EXISTS

    name = module.params['pn_name']

    show = cli + \
        ' admin-syslog-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()

    SYSLOG_EXISTS = True if name in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        present='admin-syslog-create',
        absent='admin-syslog-delete',
        update='admin-syslog-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_host=dict(required=False, type='str'),
            pn_port=dict(required=False, type='str'),
            pn_transport=dict(required=False, type='str',
                              choices=['tcp-tls', 'udp']),
            pn_message_format=dict(required=False, type='str',
                                   choices=['structured', 'legacy']),
            pn_name=dict(required=False, type='str'),
        ),
        required_if=(
            ['state', 'present', ['pn_name', 'pn_host', 'pn_scope']],
            ['state', 'absent', ['pn_name']],
            ['state', 'update', ['pn_name']]
        ),
        required_one_of=[['pn_port', 'pn_message_format',
                          'pn_host', 'pn_transport', 'pn_scope']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    scope = module.params['pn_scope']
    host = module.params['pn_host']
    port = module.params['pn_port']
    transport = module.params['pn_transport']
    message_format = module.params['pn_message_format']
    name = module.params['pn_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    check_cli(module, cli)
    cli += ' %s name %s ' % (command, name)

    if command == 'admin-syslog-modify':
        if SYSLOG_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='admin syslog with name %s does not exist' % name
            )

    if command == 'admin-syslog-delete':
        if SYSLOG_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='admin syslog with name %s does not exist' % name
            )

    if command == 'admin-syslog-create':
        if SYSLOG_EXISTS is True:
            module.exit_json(
                 skipped=True,
                 msg='admin syslog user with name %s already exists' % name
            )

    if command != 'admin-syslog-delete':
        if scope:
            cli += ' scope ' + scope
        if host:
            cli += ' host ' + host
        if port:
            cli += ' port ' + port
        if transport:
            cli += ' transport ' + transport
        if message_format:
            cli += ' message-format ' + message_format

    run_cli(module, cli)


if __name__ == '__main__':
    main()
