#!/usr/bin/python
""" PN-CLI vrouter-bgp-add/vrouter-bgp-remove/vrouter-bgp-modify """

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
module: pn_vrouterbgp
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to add/remove/modify vrouter-bgp.
description:
  - Execute vrouter-bgp-add, vrouter-bgp-remove, vrouter-bgp-modify command.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a vRouter service that forwards traffic between
    networks and implements Layer 4 protocols.
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
  state:
    description:
      - State the action to perform. Use 'present' to add bgp,
        'absent' to remove bgp and 'update' to modify bgp.
    required: True
    choices: ['present', 'absent', 'update']
  pn_vrouter_name:
    description:
      - Specify a name for the vRouter service.
    required: True
  pn_neighbor:
    description:
      - Specify a neighbor IP address to use for BGP.
      - Required for vrouter-bgp-add.
  pn_remote_as:
    description:
      - Specify the remote Autonomous System(AS) number. This value is between
        1 and 4294967295.
      - Required for vrouter-bgp-add.
  pn_next_hop_self:
    description:
      - Specify if the next-hop is the same router or not.
  pn_password:
    description:
      - Specify a password, if desired.
  pn_ebgp:
    description:
      - Specify a value for external BGP to accept or attempt BGP connections
        to external peers, not directly connected, on the network. This is a
        value between 1 and 255.
  pn_prefix_listin:
    description:
      - Specify the prefix list to filter traffic inbound.
  pn_prefix_listout:
    description:
      - Specify the prefix list to filter traffic outbound.
  pn_route_reflector:
    description:
      - Specify if a route reflector client is used.
  pn_override_capability:
    description:
      - Specify if you want to override capability.
  pn_soft_reconfig:
    description:
      - Specify if you want a soft reconfiguration of inbound traffic.
  pn_max_prefix:
    description:
      - Specify the maximum number of prefixes.
  pn_max_prefix_warn:
    description:
      - Specify if you want a warning message when the maximum number of
        prefixes is exceeded.
  pn_bfd:
    description:
      - Specify if you want BFD protocol support for fault detection.
  pn_multiprotocol:
    description:
      - Specify a multi-protocol for BGP.
    choices: ['ipv4-unicast', 'ipv6-unicast']
  pn_weight:
    description:
      - Specify a default weight value between 0 and 65535 for the neighbor
        routes.
  pn_default_originate:
    description:
      - Specify if you want announce default routes to the neighbor or not.
  pn_keepalive:
    description:
      - Specify BGP neighbor keepalive interval in seconds.
  pn_holdtime:
    description:
      - Specify BGP neighbor holdtime in seconds.
  pn_route_mapin:
    description:
      - Specify inbound route map for neighbor.
  pn_route_mapout:
    description:
      - Specify outbound route map for neighbor.
"""

EXAMPLES = """
- name: add vrouter-bgp
  pn_vrouterbgp:
    state: 'present'
    pn_vrouter_name: 'ansible-vrouter'
    pn_neighbor: 104.104.104.1
    pn_remote_as: 1800

- name: remove vrouter-bgp
  pn_vrouterbgp:
    state: 'absent'
    pn_name: 'ansible-vrouter'
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the vrouterbpg command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the vrouterbgp command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

VROUTER_EXISTS = None
NEIGHBOR_EXISTS = None


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
    This method also checks for idempotency using the vrouter-bgp-show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If a BGP neighbor with the given ip exists on the given vRouter,
    return NEIGHBOR_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, NEIGHBOR_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    neighbor = module.params['pn_neighbor']
    # Global flags
    global VROUTER_EXISTS, NEIGHBOR_EXISTS

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]
    out = out.split()

    if vrouter_name in out:
        VROUTER_EXISTS = True
    else:
        VROUTER_EXISTS = False

    # Check for BGP neighbors
    show = cli + ' vrouter-bgp-show vrouter-name %s ' % vrouter_name
    show += 'format neighbor no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    if neighbor in out:
        NEIGHBOR_EXISTS = True
    else:
        NEIGHBOR_EXISTS = False


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
        command = 'vrouter-bgp-add'
    if state == 'absent':
        command = 'vrouter-bgp-remove'
    if state == 'update':
        command = 'vrouter-bgp-modify'
    return command


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent', 'update']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_neighbor=dict(type='str'),
            pn_remote_as=dict(type='str'),
            pn_next_hop_self=dict(type='bool'),
            pn_password=dict(type='str', no_log=True),
            pn_ebgp=dict(type='int'),
            pn_prefix_listin=dict(type='str'),
            pn_prefix_listout=dict(type='str'),
            pn_route_reflector=dict(type='bool'),
            pn_override_capability=dict(type='bool'),
            pn_soft_reconfig=dict(type='bool'),
            pn_max_prefix=dict(type='int'),
            pn_max_prefix_warn=dict(type='bool'),
            pn_bfd=dict(type='bool'),
            pn_multiprotocol=dict(type='str',
                                  choices=['ipv4-unicast', 'ipv6-unicast']),
            pn_weight=dict(type='int'),
            pn_default_originate=dict(type='bool'),
            pn_keepalive=dict(type='str'),
            pn_holdtime=dict(type='str'),
            pn_route_mapin=dict(type='str'),
            pn_route_mapout=dict(type='str')
        ),
        required_if=(
            ["state", "present",
             ["pn_vrouter_name", "pn_neighbor", "pn_remote_as"]],
            ["state", "absent",
             ["pn_vrouter_name", "pn_neighbor"]],
            ["state", "update",
             ["pn_vrouter_name", "pn_neighbor"]]
        )
    )

    # Accessing the arguments
    state = module.params['state']
    vrouter_name = module.params['pn_vrouter_name']
    neighbor = module.params['pn_neighbor']
    remote_as = module.params['pn_remote_as']
    next_hop_self = module.params['pn_next_hop_self']
    password = module.params['pn_password']
    ebgp = module.params['pn_ebgp']
    prefix_listin = module.params['pn_prefix_listin']
    prefix_listout = module.params['pn_prefix_listout']
    route_reflector = module.params['pn_route_reflector']
    override_capability = module.params['pn_override_capability']
    soft_reconfig = module.params['pn_soft_reconfig']
    max_prefix = module.params['pn_max_prefix']
    max_prefix_warn = module.params['pn_max_prefix_warn']
    bfd = module.params['pn_bfd']
    multiprotocol = module.params['pn_multiprotocol']
    weight = module.params['pn_weight']
    default_originate = module.params['pn_default_originate']
    keepalive = module.params['pn_keepalive']
    holdtime = module.params['pn_holdtime']
    route_mapin = module.params['pn_route_mapin']
    route_mapout = module.params['pn_route_mapout']

    # Building the CLI command string
    cli = pn_cli(module)

    command = get_command_from_state(state)
    if command == 'vrouter-bgp-remove':
        check_cli(module, cli)
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )
        if NEIGHBOR_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('BGP neighbor with IP %s does not exist on %s'
                     % (neighbor, vrouter_name))
            )
        cli += (' %s vrouter-name %s neighbor %s '
                % (command, vrouter_name, neighbor))

    else:

        if command == 'vrouter-bgp-add':
            check_cli(module, cli)
            if VROUTER_EXISTS is False:
                module.exit_json(
                    skipped=True,
                    msg='vRouter %s does not exist' % vrouter_name
                )
            if NEIGHBOR_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg=('BGP neighbor with IP %s already exists on %s'
                         % (neighbor, vrouter_name))
                )

        cli += (' %s vrouter-name %s neighbor %s '
                % (command, vrouter_name, neighbor))

        if remote_as:
            cli += ' remote-as ' + str(remote_as)

        if next_hop_self is True:
            cli += ' next-hop-self '
        if next_hop_self is False:
            cli += ' no-next-hop-self '

        if password:
            cli += ' password ' + password

        if ebgp:
            cli += ' ebgp-multihop ' + str(ebgp)

        if prefix_listin:
            cli += ' prefix-list-in ' + prefix_listin

        if prefix_listout:
            cli += ' prefix-list-out ' + prefix_listout

        if route_reflector is True:
            cli += ' route-reflector-client '
        if route_reflector is False:
            cli += ' no-route-reflector-client '

        if override_capability is True:
            cli += ' override-capability '
        if override_capability is False:
            cli += ' no-override-capability '

        if soft_reconfig is True:
            cli += ' soft-reconfig-inbound '
        if soft_reconfig is False:
            cli += ' no-soft-reconfig-inbound '

        if max_prefix:
            cli += ' max-prefix ' + str(max_prefix)

        if max_prefix_warn is True:
            cli += ' max-prefix-warn-only '
        if max_prefix_warn is False:
            cli += ' no-max-prefix-warn-only '

        if bfd is True:
            cli += ' bfd '
        if bfd is False:
            cli += ' no-bfd '

        if multiprotocol:
            cli += ' multi-protocol ' + multiprotocol

        if weight:
            cli += ' weight ' + str(weight)

        if default_originate is True:
            cli += ' default-originate '
        if default_originate is False:
            cli += ' no-default-originate '

        if keepalive:
            cli += ' neighbor-keepalive-interval ' + keepalive

        if holdtime:
            cli += ' neighbor-holdtime ' + holdtime

        if route_mapin:
            cli += ' route-map-in ' + route_mapin

        if route_mapout:
            cli += ' route-map-out ' + route_mapout

    run_cli(module, cli)
# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
