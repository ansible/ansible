#!/usr/bin/python
""" PN CLI trunk-create/trunk-delete/trunk-modify """

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
module: pn_trunk
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to create/delete/modify a trunk.
description:
  - Execute trunk-create or trunk-delete command.
  - Trunks can be used to aggregate network links at Layer 2 on the local
    switch. Use this command to create a new trunk.
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
      - State the action to perform. Use 'present' to create trunk,
        'absent' to delete trunk and 'update' to modify trunk.
    required: True
    choices: ['present', 'absent', 'update']
  pn_name:
    description:
      - Specify the name for the trunk configuration.
    required: true
  pn_ports:
    description:
      - Specify the port number(s) for the link(s) to aggregate into the trunk.
      - Required for trunk-create.
  pn_speed:
    description:
      - Specify the port speed or disable the port.
    choices: ['disable', '10m', '100m', '1g', '2.5g', '10g', '40g']
  pn_egress_rate_limit:
    description:
      - Specify an egress port data rate limit for the configuration.
  pn_jumbo:
    description:
      - Specify if the port can receive jumbo frames.
  pn_lacp_mode:
    description:
      - Specify the LACP mode for the configuration.
    choices: ['off', 'passive', 'active']
  pn_lacp_priority:
    description:
      - Specify the LACP priority. This is a number between 1 and 65535 with a
        default value of 32768.
  pn_lacp_timeout:
    description:
      - Specify the LACP time out as slow (30 seconds) or fast (4seconds).
        The default value is slow.
    choices: ['slow', 'fast']
  pn_lacp_fallback:
    description:
      - Specify the LACP fallback mode as bundles or individual.
    choices: ['bundle', 'individual']
  pn_lacp_fallback_timeout:
    description:
      - Specify the LACP fallback timeout in seconds. The range is between 30
        and 60 seconds with a default value of 50 seconds.
  pn_edge_switch:
    description:
      - Specify if the switch is an edge switch.
  pn_pause:
    description:
      - Specify if pause frames are sent.
  pn_description:
    description:
      - Specify a description for the trunk configuration.
  pn_loopback:
    description:
      - Specify loopback if you want to use loopback.
  pn_mirror_receive:
    description:
      - Specify if the configuration receives mirrored traffic.
  pn_unknown_ucast_level:
    description:
      - Specify an unknown unicast level in percent. The default value is 100%.
  pn_unknown_mcast_level:
    description:
      - Specify an unknown multicast level in percent. The default value is 100%.
  pn_broadcast_level:
    description:
      - Specify a broadcast level in percent. The default value is 100%.
  pn_port_macaddr:
    description:
      - Specify the MAC address of the port.
  pn_loopvlans:
    description:
      - Specify a list of looping vlans.
  pn_routing:
    description:
      - Specify if the port participates in routing on the network.
  pn_host:
    description:
      - Host facing port control setting.
"""

EXAMPLES = """
- name: create trunk
  pn_trunk:
    state: 'present'
    pn_name: 'spine-to-leaf'
    pn_ports: '11,12,13,14'

- name: delete trunk
  pn_trunk:
    state: 'absent'
    pn_name: 'spine-to-leaf'
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the trunk command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the trunk command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

TRUNK_EXISTS = None


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
    This method checks for idempotency using the trunk-show command.
    If a trunk with given name exists, return TRUNK_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: TRUNK_EXISTS
    """
    name = module.params['pn_name']

    show = cli + ' trunk-show format switch,name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global TRUNK_EXISTS
    if name in out:
        TRUNK_EXISTS = True
    else:
        TRUNK_EXISTS = False


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
        command = 'trunk-create'
    if state == 'absent':
        command = 'trunk-delete'
    if state == 'update':
        command = 'trunk-modify'
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
            pn_name=dict(required=True, type='str'),
            pn_ports=dict(type='str'),
            pn_speed=dict(type='str',
                          choices=['disable', '10m', '100m', '1g', '2.5g',
                                   '10g', '40g']),
            pn_egress_rate_limit=dict(type='str'),
            pn_jumbo=dict(type='bool'),
            pn_lacp_mode=dict(type='str', choices=[
                              'off', 'passive', 'active']),
            pn_lacp_priority=dict(type='int'),
            pn_lacp_timeout=dict(type='str'),
            pn_lacp_fallback=dict(type='str', choices=[
                                  'bundle', 'individual']),
            pn_lacp_fallback_timeout=dict(type='str'),
            pn_edge_switch=dict(type='bool'),
            pn_pause=dict(type='bool'),
            pn_description=dict(type='str'),
            pn_loopback=dict(type='bool'),
            pn_mirror_receive=dict(type='bool'),
            pn_unknown_ucast_level=dict(type='str'),
            pn_unknown_mcast_level=dict(type='str'),
            pn_broadcast_level=dict(type='str'),
            pn_port_macaddr=dict(type='str'),
            pn_loopvlans=dict(type='str'),
            pn_routing=dict(type='bool'),
            pn_host=dict(type='bool')
        ),
        required_if=(
            ["state", "present", ["pn_name", "pn_ports"]],
            ["state", "absent", ["pn_name"]],
            ["state", "update", ["pn_name"]]
        )
    )

    # Accessing the arguments
    state = module.params['state']
    name = module.params['pn_name']
    ports = module.params['pn_ports']
    speed = module.params['pn_speed']
    egress_rate_limit = module.params['pn_egress_rate_limit']
    jumbo = module.params['pn_jumbo']
    lacp_mode = module.params['pn_lacp_mode']
    lacp_priority = module.params['pn_lacp_priority']
    lacp_timeout = module.params['pn_lacp_timeout']
    lacp_fallback = module.params['pn_lacp_fallback']
    lacp_fallback_timeout = module.params['pn_lacp_fallback_timeout']
    edge_switch = module.params['pn_edge_switch']
    pause = module.params['pn_pause']
    description = module.params['pn_description']
    loopback = module.params['pn_loopback']
    mirror_receive = module.params['pn_mirror_receive']
    unknown_ucast_level = module.params['pn_unknown_ucast_level']
    unknown_mcast_level = module.params['pn_unknown_mcast_level']
    broadcast_level = module.params['pn_broadcast_level']
    port_macaddr = module.params['pn_port_macaddr']
    loopvlans = module.params['pn_loopvlans']
    routing = module.params['pn_routing']
    host = module.params['pn_host']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'trunk-delete':

        check_cli(module, cli)
        if TRUNK_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Trunk with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)

    else:
        if command == 'trunk-create':
            check_cli(module, cli)
            if TRUNK_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='Trunk with name %s already exists' % name
                )
        cli += ' %s name %s ' % (command, name)

        # Appending options
        if ports:
            cli += ' ports ' + ports

        if speed:
            cli += ' speed ' + speed

        if egress_rate_limit:
            cli += ' egress-rate-limit ' + egress_rate_limit

        if jumbo is True:
            cli += ' jumbo '
        if jumbo is False:
            cli += ' no-jumbo '

        if lacp_mode:
            cli += ' lacp-mode ' + lacp_mode

        if lacp_priority:
            cli += ' lacp-priority ' + lacp_priority

        if lacp_timeout:
            cli += ' lacp-timeout ' + lacp_timeout

        if lacp_fallback:
            cli += ' lacp-fallback ' + lacp_fallback

        if lacp_fallback_timeout:
            cli += ' lacp-fallback-timeout ' + lacp_fallback_timeout

        if edge_switch is True:
            cli += ' edge-switch '
        if edge_switch is False:
            cli += ' no-edge-switch '

        if pause is True:
            cli += ' pause '
        if pause is False:
            cli += ' no-pause '

        if description:
            cli += ' description ' + description

        if loopback is True:
            cli += ' loopback '
        if loopback is False:
            cli += ' no-loopback '

        if mirror_receive is True:
            cli += ' mirror-receive-only '
        if mirror_receive is False:
            cli += ' no-mirror-receive-only '

        if unknown_ucast_level:
            cli += ' unknown-ucast-level ' + unknown_ucast_level

        if unknown_mcast_level:
            cli += ' unknown-mcast-level ' + unknown_mcast_level

        if broadcast_level:
            cli += ' broadcast-level ' + broadcast_level

        if port_macaddr:
            cli += ' port-mac-address ' + port_macaddr

        if loopvlans:
            cli += ' loopvlans ' + loopvlans

        if routing is True:
            cli += ' routing '
        if routing is False:
            cli += ' no-routing '

        if host is True:
            cli += ' host-enable '
        if host is False:
            cli += ' host-disable '

    run_cli(module, cli)

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
