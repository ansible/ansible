#!/usr/bin/python
""" PN CLI snmp-vacm-create/modify/delete """
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_snmp_vacm
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/modify/delete snmp-vacm.
description:
  - C(create): create View Access Control Models (VACM)
  - C(modify): modify View Access Control Models (VACM)
  - C(delete): delete View Access Control Models (VACM)
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
  state:
    description:
      - State the action to perform. Use 'present' to create snmp-vacm and
        'absent' to delete snmp-vacm and 'update' to modify snmp-vacm.
    required: True
  pn_oid_restrict:
    description:
      - restrict OID
    type: str
  pn_priv:
    description:
      - privileges
  pn_auth:
    description:
      - authentication required
  pn_user_type:
    description:
      - SNMP user type
    choices: ['rouser', 'rwuser']
  pn_user_name:
    description:
      - SNMP administrator name
    type: str
"""

EXAMPLES = """
- name: snmp vacm functionality
  pn_snmp_vacm:
    state: "present"
    pn_user_name: "VINETro"
    pn_auth: True
    pn_priv: True
    pn_user_type: "rouser"

- name: snmp vacm functionality
  pn_snmp_vacm:
    state: "update"
    pn_user_name: "VINETro"
    pn_auth: True
    pn_priv: True
    pn_user_type: "rwuser"

- name: snmp vacm functionality
  pn_snmp_vacm:
    state: "absent"
    pn_user_name: "VINETro"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the snmp-vacm command.
  returned: always
  type: list
stderr:
  description: set of error responses from the snmp-vacm command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli
from ansible.module_utils.pn_nvos import booleanArgs


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
    This method checks for idempotency using the snmp-vacm-show command.
    If a user with given name exists, return USER_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: USER_EXISTS
    """
    user_name = module.params['pn_user_name']

    show = cli + \
        ' snmp-vacm-show format user-name no-show-headers'
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
        present='snmp-vacm-create',
        absent='snmp-vacm-delete',
        update='snmp-vacm-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_oid_restrict=dict(required=False, type='str'),
            pn_priv=dict(required=False, type='bool'),
            pn_auth=dict(required=False, type='bool'),
            pn_user_type=dict(required=False, type='str',
                              choices=['rouser', 'rwuser']),
            pn_user_name=dict(required=False, type='str'),
        ),
        required_if=(
            ["state", "present", ["pn_user_name"]],
            ["state", "absent", ["pn_user_name"]],
            ["state", "update", ["pn_user_name"]]
        )

    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    oid_restrict = module.params['pn_oid_restrict']
    priv = module.params['pn_priv']
    auth = module.params['pn_auth']
    user_type = module.params['pn_user_type']
    user_name = module.params['pn_user_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    check_cli(module, cli)
    cli += ' %s user-name %s ' % (command, user_name)

    if command == 'snmp-vacm-modify':
        if USER_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='snmp vacm with name %s doesnt exists' % user_name
            )

    if command == 'snmp-vacm-delete':
        if USER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='snmp-vacm with name %s does not exist' % user_name
            )

    if command == 'snmp-vacm-create':
        if USER_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='snmp vacm with name %s already exists' % user_name
            )

    if command != 'snmp-vacm-delete':
        if oid_restrict:
            cli += ' oid-restrict ' + oid_restrict
        if user_type:
            cli += ' user-type ' + user_type

        cli += booleanArgs(auth, 'auth', 'no-auth')
        cli += booleanArgs(priv, 'priv', 'no-priv')

    run_cli(module, cli)


if __name__ == '__main__':
    main()
