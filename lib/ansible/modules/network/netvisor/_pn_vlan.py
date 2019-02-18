#!/usr/bin/python
""" PN CLI vlan-create/vlan-delete """

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
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_vlan
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to create/delete a VLAN.
deprecated:
  removed_in: '2.12'
  why: Doesn't support latest Pluribus Networks netvisor
  alternative: Latest modules will be pushed in Ansible future versions.
description:
  - Execute vlan-create or vlan-delete command.
  - VLANs are used to isolate network traffic at Layer 2.The VLAN identifiers
    0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard.
    The range of configurable VLAN identifiers is 2 through 4092.
options:
  pn_cliusername:
    description:
      - Provide login username if user is not root.
    required: False
  pn_clipassword:
    description:
      - Provide login password if user is not root.
    required: False
  pn_cliswitch:
    description:
      - Target switch(es) to run the cli on.
    required: False
    default: 'local'
  state:
    description:
      - State the action to perform. Use 'present' to create vlan and
        'absent' to delete vlan.
    required: True
    choices: ['present', 'absent']
  pn_vlanid:
    description:
      - Specify a VLAN identifier for the VLAN. This is a value between
        2 and 4092.
    required: True
  pn_scope:
    description:
      - Specify a scope for the VLAN.
      - Required for vlan-create.
    choices: ['fabric', 'local']
  pn_description:
    description:
      - Specify a description for the VLAN.
  pn_stats:
    description:
      - Specify if you want to collect statistics for a VLAN. Statistic
        collection is enabled by default.
    type: bool
  pn_ports:
    description:
      - Specifies the switch network data port number, list of ports, or range
        of ports. Port numbers must ne in the range of 1 to 64.
  pn_untagged_ports:
    description:
      - Specifies the ports that should have untagged packets mapped to the
        VLAN. Untagged packets are packets that do not contain IEEE 802.1Q VLAN
        tags.
"""

EXAMPLES = """
- name: create a VLAN
  pn_vlan:
    state: 'present'
    pn_vlanid: 1854
    pn_scope: fabric

- name: delete VLANs
  pn_vlan:
    state: 'absent'
    pn_vlanid: 1854
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the vlan command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the vlan command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

VLAN_EXISTS = None
MAX_VLAN_ID = 4092
MIN_VLAN_ID = 2


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch == 'local':
        cli += ' switch-local '
    else:
        cli += ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks for idempotency using the vlan-show command.
    If a vlan with given vlan id exists, return VLAN_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VLAN_EXISTS
    """
    vlanid = module.params['pn_vlanid']

    show = cli + \
        ' vlan-show id %s format id,scope no-show-headers' % str(vlanid)
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global VLAN_EXISTS
    if str(vlanid) in out:
        VLAN_EXISTS = True
    else:
        VLAN_EXISTS = False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    command = get_command_from_state(state)

    cmd = shlex.split(cli)
    # 'out' contains the output
    # 'err' contains the error messages
    result, out, err = module.run_command(cmd)

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format

    if result != 0:
        module.exit_json(
            command=print_cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=print_cli,
            msg="%s operation completed" % command,
            changed=True
        )


def get_command_from_state(state):
    """
    This method gets appropriate command name for the state specified. It
    returns the command name for the specified state.
    :param state: The state for which the respective command name is required.
    """
    command = None
    if state == 'present':
        command = 'vlan-create'
    if state == 'absent':
        command = 'vlan-delete'
    return command


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            pn_vlanid=dict(required=True, type='int'),
            pn_scope=dict(type='str', choices=['fabric', 'local']),
            pn_description=dict(type='str'),
            pn_stats=dict(type='bool'),
            pn_ports=dict(type='str'),
            pn_untagged_ports=dict(type='str')
        ),
        required_if=(
            ["state", "present", ["pn_vlanid", "pn_scope"]],
            ["state", "absent", ["pn_vlanid"]]
        )
    )

    # Accessing the arguments
    state = module.params['state']
    vlanid = module.params['pn_vlanid']
    scope = module.params['pn_scope']
    description = module.params['pn_description']
    stats = module.params['pn_stats']
    ports = module.params['pn_ports']
    untagged_ports = module.params['pn_untagged_ports']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    if not MIN_VLAN_ID <= vlanid <= MAX_VLAN_ID:
        module.exit_json(
            msg="VLAN id must be between 2 and 4092",
            changed=False
        )

    if command == 'vlan-create':

        check_cli(module, cli)
        if VLAN_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='VLAN with id %s already exists' % str(vlanid)
            )

        cli += ' %s id %s scope %s ' % (command, str(vlanid), scope)

        if description:
            cli += ' description ' + description

        if stats is True:
            cli += ' stats '
        if stats is False:
            cli += ' no-stats '

        if ports:
            cli += ' ports ' + ports

        if untagged_ports:
            cli += ' untagged-ports ' + untagged_ports

    if command == 'vlan-delete':

        check_cli(module, cli)
        if VLAN_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='VLAN with id %s does not exist' % str(vlanid)
            )

        cli += ' %s id %s ' % (command, str(vlanid))

    run_cli(module, cli)


if __name__ == '__main__':
    main()
