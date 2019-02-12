#!/usr/bin/python
""" PN CLI vrouter-loopback-interface-add/remove """

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
module: pn_vrouterlbif
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to add/remove vrouter-loopback-interface.
deprecated:
  removed_in: '2.12'
  why: Doesn't support latest Pluribus Networks netvisor
  alternative: Latest modules will be pushed in Ansible future versions.
description:
  - Execute vrouter-loopback-interface-add, vrouter-loopback-interface-remove
    commands.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a virtual router (vRouter) service that forwards
    traffic between networks and implements Layer 3 protocols.
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
      - State the action to perform. Use 'present' to add vrouter loopback
        interface and 'absent' to remove vrouter loopback interface.
    required: True
    choices: ['present', 'absent']
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter.
    required: True
  pn_index:
    description:
      - Specify the interface index from 1 to 255.
  pn_interface_ip:
    description:
      - Specify the IP address.
    required: True
"""

EXAMPLES = """
- name: add vrouter-loopback-interface
  pn_vrouterlbif:
    state: 'present'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: '104.104.104.1'

- name: remove vrouter-loopback-interface
  pn_vrouterlbif:
    state: 'absent'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: '104.104.104.1'
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the vrouterlb command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the vrouterlb command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

VROUTER_EXISTS = None
LB_INTERFACE_EXISTS = None
# Index range
MIN_INDEX = 1
MAX_INDEX = 255


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
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the
    vrouter-loopback-interface-show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If a loopback interface with the given ip exists on the given vRouter,
    return LB_INTERFACE_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, LB_INTERFACE_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']

    # Global flags
    global VROUTER_EXISTS, LB_INTERFACE_EXISTS

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]
    out = out.split()

    if vrouter_name in out:
        VROUTER_EXISTS = True
    else:
        VROUTER_EXISTS = False

    # Check for loopback interface
    show = (cli + ' vrouter-loopback-interface-show vrouter-name %s format ip '
            'no-show-headers' % vrouter_name)
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    if interface_ip in out:
        LB_INTERFACE_EXISTS = True
    else:
        LB_INTERFACE_EXISTS = False


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
        command = 'vrouter-loopback-interface-add'
    if state == 'absent':
        command = 'vrouter-loopback-interface-remove'
    return command


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_interface_ip=dict(type='str'),
            pn_index=dict(type='int')
        ),
        required_if=(
            ["state", "present",
             ["pn_vrouter_name", "pn_interface_ip"]],
            ["state", "absent",
             ["pn_vrouter_name", "pn_interface_ip"]]
        )
    )

    # Accessing the arguments
    state = module.params['state']
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']
    index = module.params['pn_index']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    if index:
        if not MIN_INDEX <= index <= MAX_INDEX:
            module.exit_json(
                msg="Index must be between 1 and 255",
                changed=False
            )
        index = str(index)

    if command == 'vrouter-loopback-interface-remove':
        check_cli(module, cli)
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )
        if LB_INTERFACE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('Loopback interface with IP %s does not exist on %s'
                     % (interface_ip, vrouter_name))
            )
        if not index:
            # To remove loopback interface, we need the index.
            # If index is not specified, get the Loopback interface index
            # using the given interface ip.
            get_index = cli
            get_index += (' vrouter-loopback-interface-show vrouter-name %s ip '
                          '%s ' % (vrouter_name, interface_ip))
            get_index += 'format index no-show-headers'

            get_index = shlex.split(get_index)
            out = module.run_command(get_index)[1]
            index = out.split()[1]

        cli += ' %s vrouter-name %s index %s' % (command, vrouter_name, index)

    if command == 'vrouter-loopback-interface-add':
        check_cli(module, cli)
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('vRouter %s does not exist' % vrouter_name)
            )
        if LB_INTERFACE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg=('Loopback interface with IP %s already exists on %s'
                     % (interface_ip, vrouter_name))
            )
        cli += (' %s vrouter-name %s ip %s'
                % (command, vrouter_name, interface_ip))
        if index:
            cli += ' index %s ' % index

    run_cli(module, cli)


if __name__ == '__main__':
    main()
