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
module: pn_admin_syslog
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete admin-syslog
description:
  - This module can be used to create the scope and other parameters of syslog event collection.
  - This module can be used to modify parameters of syslog event collection.
  - This module can be used to delete the scope and other parameters of syslog event collection.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create admin-syslog and
        C(absent) to delete admin-syslog C(update) to modify the admin-syslog.
    required: True
    type: str
    choices: ['present', 'absent', 'update']
  pn_scope:
    description:
      - Scope of the system log.
    required: False
    type: str
    choices: ['local', 'fabric']
  pn_host:
    description:
      - Hostname to log system events.
    required: False
    type: str
  pn_port:
    description:
      - Host port.
    required: False
    type: str
  pn_transport:
    description:
      - Transport for log events - tcp/tls or udp.
    required: False
    type: str
    choices: ['tcp-tls', 'udp']
    default: 'udp'
  pn_message_format:
    description:
      - message-format for log events - structured or legacy.
    required: False
    choices: ['structured', 'legacy']
    type: str
  pn_name:
    description:
      - name of the system log.
    required: False
    type: str
"""

EXAMPLES = """
- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_name: "foo"
    pn_scope: "local"

- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: "sw01"
    state: "present"
    pn_name: "foo"
    pn_scope: "local"
    pn_host: "166.68.224.46"
    pn_message_format: "structured"

- name: admin-syslog functionality
  pn_admin_syslog:
    pn_cliswitch: "sw01"
    state: "update"
    pn_name: "foo"
    pn_host: "166.68.224.10"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module, cli):
    """
    This method checks for idempotency using the admin-syslog-show command.
    If a user with given name exists, return as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """

    name = module.params['pn_name']

    cli += ' admin-syslog-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

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
                              choices=['tcp-tls', 'udp'], default='udp'),
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

    SYSLOG_EXISTS = check_cli(module, cli)
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

    if command == 'admin-syslog-create':
        if scope:
            cli += ' scope ' + scope

    if command != 'admin-syslog-delete':
        if host:
            cli += ' host ' + host
        if port:
            cli += ' port ' + port
        if transport:
            cli += ' transport ' + transport
        if message_format:
            cli += ' message-format ' + message_format

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
