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
module: pn_snmp_vacm
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/modify/delete snmp-vacm
description:
  - This module can be used to create View Access Control Models (VACM),
    modify VACM and delete VACM.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    type: str
    required: false
  state:
    description:
      - State the action to perform. Use C(present) to create snmp-vacm and
        C(absent) to delete snmp-vacm and C(update) to modify snmp-vacm.
    type: str
    required: true
    choices: ['present', 'absent', 'update']
  pn_oid_restrict:
    description:
      - restrict OID.
    type: str
  pn_priv:
    description:
      - privileges.
    type: bool
  pn_auth:
    description:
      - authentication required.
    type: bool
  pn_user_type:
    description:
      - SNMP user type.
    type: str
    choices: ['rouser', 'rwuser']
  pn_user_name:
    description:
      - SNMP administrator name.
    type: str
"""

EXAMPLES = """
- name: create snmp vacm
  pn_snmp_vacm:
    pn_cliswitch: "sw01"
    state: "present"
    pn_user_name: "foo"
    pn_user_type: "rouser"

- name: update snmp vacm
  pn_snmp_vacm:
    pn_cliswitch: "sw01"
    state: "update"
    pn_user_name: "foo"
    pn_user_type: "rwuser"

- name: delete snmp vacm
  pn_snmp_vacm:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_user_name: "foo"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
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


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module, cli):
    """
    This method checks for idempotency using the snmp-vacm-show command.
    If a user with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    user_name = module.params['pn_user_name']
    show = cli

    cli += ' snmp-user-show format user-name no-show-headers'
    rc, out, err = run_commands(module, cli)

    if out and user_name in out.split():
        pass
    else:
        return None

    cli = show
    cli += ' snmp-vacm-show format user-name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if user_name in out else False


def main():
    """ This section is for arguments parsing """

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

    USER_EXISTS = check_cli(module, cli)
    cli += ' %s user-name %s ' % (command, user_name)

    if command == 'snmp-vacm-modify':
        if USER_EXISTS is None:
            module.fail_json(
                failed=True,
                msg='snmp user with name %s does not exists' % user_name
            )
        if USER_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='snmp vacm with name %s does not exists' % user_name
            )

    if command == 'snmp-vacm-delete':
        if USER_EXISTS is None:
            module.fail_json(
                failed=True,
                msg='snmp user with name %s does not exists' % user_name
            )

        if USER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='snmp vacm with name %s does not exist' % user_name
            )

    if command == 'snmp-vacm-create':
        if USER_EXISTS is None:
            module.fail_json(
                failed=True,
                msg='snmp user with name %s does not exists' % user_name
            )
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

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
