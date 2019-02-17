#!/usr/bin/python
""" PN CLI vrouter-create/vrouter-delete/vrouter-modify """

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
module: pn_vrouter
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to create/delete/modify a vrouter.
deprecated:
  removed_in: '2.12'
  why: Doesn't support latest Pluribus Networks netvisor
  alternative: Latest modules will be pushed in Ansible future versions.
description:
  - Execute vrouter-create, vrouter-delete, vrouter-modify command.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a virtual router (vRouter) service that forwards
    traffic between networks and implements Layer 3 protocols.
  - C(vrouter-create) creates a new vRouter service.
  - C(vrouter-delete) deletes a vRouter service.
  - C(vrouter-modify) modifies a vRouter service.
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
      - Target switch(es) to run the CLI on.
    required: False
    default: 'local'
  state:
    description:
      - State the action to perform. Use 'present' to create vrouter,
        'absent' to delete vrouter and 'update' to modify vrouter.
    required: True
    choices: ['present', 'absent', 'update']
  pn_name:
    description:
      - Specify the name of the vRouter.
    required: true
  pn_vnet:
    description:
      - Specify the name of the VNET.
      - Required for vrouter-create.
  pn_service_type:
    description:
      - Specify if the vRouter is a dedicated or shared VNET service.
    choices: ['dedicated', 'shared']
  pn_service_state:
    description:
      -  Specify to enable or disable vRouter service.
    choices: ['enable', 'disable']
  pn_router_type:
    description:
      - Specify if the vRouter uses software or hardware.
      - Note that if you specify hardware as router type, you cannot assign IP
        addresses using DHCP. You must specify a static IP address.
    choices: ['hardware', 'software']
  pn_hw_vrrp_id:
    description:
      - Specifies the VRRP ID for a hardware vrouter.
  pn_router_id:
    description:
      - Specify the vRouter IP address.
  pn_bgp_as:
    description:
      - Specify the Autonomous System Number(ASN) if the vRouter runs Border
        Gateway Protocol(BGP).
  pn_bgp_redistribute:
    description:
      - Specify how BGP routes are redistributed.
    choices: ['static', 'connected', 'rip', 'ospf']
  pn_bgp_max_paths:
    description:
      - Specify the maximum number of paths for BGP. This is a number between
        1 and 255 or 0 to unset.
  pn_bgp_options:
    description:
      - Specify other BGP options as a whitespaces separated string within
        single quotes ''.
  pn_rip_redistribute:
    description:
      - Specify how RIP routes are redistributed.
    choices: ['static', 'connected', 'ospf', 'bgp']
  pn_ospf_redistribute:
    description:
      - Specify how OSPF routes are redistributed.
    choices: ['static', 'connected', 'bgp', 'rip']
  pn_ospf_options:
    description:
      - Specify other OSPF options as a whitespaces separated string within
        single quotes ''.
  pn_vrrp_track_port:
    description:
      - Specify list of ports and port ranges.
"""

EXAMPLES = """
- name: create vrouter
  pn_vrouter:
    state: 'present'
    pn_name: 'ansible-vrouter'
    pn_vnet: 'ansible-fab-global'
    pn_router_id: 208.74.182.1

- name: delete vrouter
  pn_vrouter:
    state: 'absent'
    pn_name: 'ansible-vrouter'
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the vrouter command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the vrouter command.
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

VROUTER_EXISTS = None
VROUTER_NAME_EXISTS = None


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
    A switch can have only one vRouter configuration.
    If a vRouter already exists on the given switch, return VROUTER_EXISTS as
    True else False.
    If a vRouter with the given name exists(on a different switch), return
    VROUTER_NAME_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, VROUTER_NAME_EXISTS
    """
    name = module.params['pn_name']
    # Global flags
    global VROUTER_EXISTS, VROUTER_NAME_EXISTS

    # Get the name of the local switch
    location = cli + ' switch-setup-show format switch-name'
    location = shlex.split(location)
    out = module.run_command(location)[1]
    location = out.split()[1]

    # Check for any vRouters on the switch
    check_vrouter = cli + ' vrouter-show location %s ' % location
    check_vrouter += 'format name no-show-headers'
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]

    if out:
        VROUTER_EXISTS = True
    else:
        VROUTER_EXISTS = False

    # Check for any vRouters with the given name
    show = cli + ' vrouter-show format name no-show-headers '
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    if name in out:
        VROUTER_NAME_EXISTS = True
    else:
        VROUTER_NAME_EXISTS = False


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
        command = 'vrouter-create'
    if state == 'absent':
        command = 'vrouter-delete'
    if state == 'update':
        command = 'vrouter-modify'
    return command


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent', 'update']),
            pn_name=dict(required=True, type='str'),
            pn_vnet=dict(type='str'),
            pn_service_type=dict(type='str', choices=['dedicated', 'shared']),
            pn_service_state=dict(type='str', choices=['enable', 'disable']),
            pn_router_type=dict(type='str', choices=['hardware', 'software']),
            pn_hw_vrrp_id=dict(type='int'),
            pn_router_id=dict(type='str'),
            pn_bgp_as=dict(type='int'),
            pn_bgp_redistribute=dict(type='str', choices=['static', 'connected',
                                                          'rip', 'ospf']),
            pn_bgp_max_paths=dict(type='int'),
            pn_bgp_options=dict(type='str'),
            pn_rip_redistribute=dict(type='str', choices=['static', 'connected',
                                                          'bgp', 'ospf']),
            pn_ospf_redistribute=dict(type='str', choices=['static', 'connected',
                                                           'bgp', 'rip']),
            pn_ospf_options=dict(type='str'),
            pn_vrrp_track_port=dict(type='str')
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_vnet"]],
            ["state", "absent", ["pn_name"]],
            ["state", "update", ["pn_name"]]
        )
    )

    # Accessing the arguments
    state = module.params['state']
    name = module.params['pn_name']
    vnet = module.params['pn_vnet']
    service_type = module.params['pn_service_type']
    service_state = module.params['pn_service_state']
    router_type = module.params['pn_router_type']
    hw_vrrp_id = module.params['pn_hw_vrrp_id']
    router_id = module.params['pn_router_id']
    bgp_as = module.params['pn_bgp_as']
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_max_paths = module.params['pn_bgp_max_paths']
    bgp_options = module.params['pn_bgp_options']
    rip_redistribute = module.params['pn_rip_redistribute']
    ospf_redistribute = module.params['pn_ospf_redistribute']
    ospf_options = module.params['pn_ospf_options']
    vrrp_track_port = module.params['pn_vrrp_track_port']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'vrouter-delete':
        check_cli(module, cli)
        if VROUTER_NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)

    else:

        if command == 'vrouter-create':
            check_cli(module, cli)
            if VROUTER_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='Maximum number of vRouters has been reached on this '
                        'switch'
                )
            if VROUTER_NAME_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='vRouter with name %s already exists' % name
                )
        cli += ' %s name %s ' % (command, name)

        if vnet:
            cli += ' vnet ' + vnet

        if service_type:
            cli += ' %s-vnet-service ' % service_type

        if service_state:
            cli += ' ' + service_state

        if router_type:
            cli += ' router-type ' + router_type

        if hw_vrrp_id:
            cli += ' hw-vrrp-id ' + str(hw_vrrp_id)

        if router_id:
            cli += ' router-id ' + router_id

        if bgp_as:
            cli += ' bgp-as ' + str(bgp_as)

        if bgp_redistribute:
            cli += ' bgp-redistribute ' + bgp_redistribute

        if bgp_max_paths:
            cli += ' bgp-max-paths ' + str(bgp_max_paths)

        if bgp_options:
            cli += ' %s ' % bgp_options

        if rip_redistribute:
            cli += ' rip-redistribute ' + rip_redistribute

        if ospf_redistribute:
            cli += ' ospf-redistribute ' + ospf_redistribute

        if ospf_options:
            cli += ' %s ' % ospf_options

        if vrrp_track_port:
            cli += ' vrrp-track-port ' + vrrp_track_port

    run_cli(module, cli)


if __name__ == '__main__':
    main()
