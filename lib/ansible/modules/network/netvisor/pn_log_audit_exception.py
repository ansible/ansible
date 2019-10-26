#!/usr/bin/python
# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/license/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_log_audit_exception
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to create/delete an audit exception
description:
  - This module can be used to create an audit exception and delete an audit exception.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  pn_audit_type:
    description:
      - Specify the type of audit exception.
    required: false
    type: str
    choices: ['cli', 'shell', 'vtysh']
  state:
    description:
      - State the action to perform. Use 'present' to create audit-exception and
        'absent' to delete audit-exception.
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  pn_pattern:
    description:
      - Specify a regular expression to match exceptions.
    required: false
    type: str
  pn_scope:
    description:
      - scope - local or fabric.
    required: false
    type: str
    choices: ['local', 'fabric']
  pn_access:
    description:
      - Specify the access type to match exceptions.
    required: true
    type: str
    choices: ['any', 'read-only', 'read-write']
"""

EXAMPLES = """
- name: create a log-audit-exception
  pn_log_audit_exception:
    pn_audit_type: "cli"
    pn_pattern: "test"
    state: "present"
    pn_access: "any"
    pn_scope: "local"

- name: delete a log-audit-exception
  pn_log_audit_exception:
    pn_audit_type: "shell"
    pn_pattern: "test"
    state: "absent"
    pn_access: "any"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the pn_log_audit_exceptions command.
  returned: always
  type: list
stderr:
  description: set of error responses from the log_audit_exceptions command.
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
    This method checks for idempotency using the log-audit-exception command.
    If a list with given name exists, return exists as True else False.
    :param module: The Ansible module to fetch input parameters.
    :return Booleans: True or False.
    """
    state = module.params['state']
    audit_type = module.params['pn_audit_type']
    pattern = module.params['pn_pattern']
    access = module.params['pn_access']
    scope = module.params['pn_scope']
    cli += ' log-audit-exception-show'
    cli += ' no-show-headers format '
    cli += ' type,pattern,access,scope parsable-delim DELIM'

    stdout = run_commands(module, cli)[1]

    if stdout:
        linelist = stdout.strip().split('\n')
        for line in linelist:
            wordlist = line.split('DELIM')
            count = 0

            if wordlist[0] == audit_type:
                count += 1
            if wordlist[1] == pattern:
                count += 1
            if wordlist[2] == access:
                count += 1
            if state == 'present' and wordlist[3] == scope:
                count += 1
            elif state == 'absent' and count == 3:
                return True
            if state == 'present' and count == 4:
                return True

    return False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='log-audit-exception-create',
        absent='log-audit-exception-delete',
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        pn_pattern=dict(required=True, type='str'),
        state=dict(required=False, type='str',
                   choices=state_map.keys(), default='present'),
        pn_access=dict(required=True, type='str', choices=['any', 'read-only', 'read-write']),
        pn_audit_type=dict(required=True, type='str', choices=['cli', 'shell', 'vtysh']),
        pn_scope=dict(required=False, type='str', choices=['local', 'fabric']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ["pn_scope"]],
        ),
    )

    # Accessing the arguments

    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    access = module.params['pn_access']
    audit_type = module.params['pn_audit_type']
    pattern = module.params['pn_pattern']
    scope = module.params['pn_scope']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    audit_log_exists = check_cli(module, cli)

    cli += ' %s %s pattern %s %s' % (command, audit_type, pattern, access)

    if state == 'absent':
        if audit_log_exists is False:
            module.exit_json(
                skipped=True,
                msg='This audit log exception entry does not exist'
            )
        run_cli(module, cli, state_map)

    elif state == 'present':
        if audit_log_exists is True:
            module.exit_json(
                skipped=True,
                msg='This audit log exception entry already exists'
            )
        cli += ' scope %s ' % scope
        run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
