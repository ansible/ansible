#!/usr/bin/python
""" PN CLI port-config-modify """
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
module: pn_port_config
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version: 2.7
short_description: CLI command to modify port-config.
description:
  - C(modify): modify a port configuration
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'update' to modify the port-config.
    required: True
  pn_intf:
    description:
      - physical interface
    required: false
    type: str
  pn_crc_check_enable:
    description:
      - CRC check on ingress and rewrite on egress
    required: false
    type: bool
  pn_dscp_map:
    description:
      - DSCP map name to enable on port
    required: false
    type: str
  pn_autoneg:
    description:
      - physical port autonegotiation
    required: false
    type: bool
  pn_speed:
    description:
      - physical port speed
    required: false
    choices: ['disable', '10m', '100m', '1g',
              '2.5g', '10g', '25g', '40g', '50g', '100g']
  pn_port:
    description:
      - physical port
    required: false
    type: str
  pn_vxlan_termination:
    description:
      - physical port vxlan termination setting
    required: false
    type: bool
  pn_pause:
    description:
      - physical port pause
    required: false
    type: bool
  pn_loopback:
    description:
      - physical port loopback
    required: false
    type: bool
  pn_loop_vlans:
    description:
      - looping vlans
    required: false
    type: str
  pn_routing:
    description:
      - routing
    required: false
    type: bool
  pn_edge_switch:
    description:
      - physical port edge switch
    required: false
    type: bool
  pn_enable:
    description:
      - physical port enable
    required: false
    type: bool
  pn_description:
    description:
      - physical port description
    required: false
    type: str
  pn_host_enable:
    description:
      - Host facing port control setting
    required: false
    type: bool
  pn_allowed_tpid:
    description:
      - Allowed TPID in addition to 0x8100 on Vlan header
    required: false
    choices: ['vlan', 'q-in-q', 'q-in-q-old']
  pn_mirror_only:
    description:
      - physical port mirror only
    required: false
    type: bool
  pn_reflect:
    description:
      - physical port reflection
    required: false
    type: bool
  pn_jumbo:
    description:
      - jumbo frames on physical port
    required: false
    type: bool
  pn_egress_rate_limit:
    description:
      - max egress port data rate limit
    required: false
    type: str
  pn_eth_mode:
    description:
      - physical Ethernet mode
    required: false
    choices: ['1000base-x', 'sgmii', 'disabled', 'GMII']
  pn_fabric_guard:
    description:
      - Fabric guard contfiguration
    required: false
    type: bool
  pn_local_switching:
    description:
      - no-local-switching port cannot bridge traffic to
        another no-local-switching port
    required: false
    type: bool
  pn_lacp_priority:
    description:
      - LACP priority from 1 to 65535 - default 32768
    required: false
    type: str
  pn_send_port:
    description:
      - send port
    required: false
    type: str
  pn_port_mac_address:
    description:
      - physical port MAC Address
    required: false
    type: str
  pn_defer_bringup:
    description:
      - defer port bringup
    required: false
    type: bool
"""

EXAMPLES = """
- name: port config modify
  pn_port_config:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "all"
    pn_dscp_map: "foo"

- name: port config modify
  pn_port_config:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "all"
    pn_host_enable: True
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the port-config command.
  returned: always
  type: list
stderr:
  description: set of error responses from the port-config command.
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


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        update='port-config-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=['update']),
            pn_intf=dict(required=False, type='str'),
            pn_crc_check_enable=dict(required=False, type='bool'),
            pn_dscp_map=dict(required=False, type='str'),
            pn_autoneg=dict(required=False, type='bool'),
            pn_speed=dict(required=False, type='str',
                          choices=['disable', '10m', '100m',
                                   '1g', '2.5g', '10g', '25g',
                                   '40g', '50g', '100g']),
            pn_port=dict(required=False, type='str'),
            pn_vxlan_termination=dict(required=False, type='bool'),
            pn_pause=dict(required=False, type='bool'),
            pn_loopback=dict(required=False, type='bool'),
            pn_loop_vlans=dict(required=False, type='str'),
            pn_routing=dict(required=False, type='bool'),
            pn_edge_switch=dict(required=False, type='bool'),
            pn_enable=dict(required=False, type='bool'),
            pn_description=dict(required=False, type='str'),
            pn_host_enable=dict(required=False, type='bool'),
            pn_allowed_tpid=dict(required=False, type='str',
                                 choices=['vlan', 'q-in-q', 'q-in-q-old']),
            pn_mirror_only=dict(required=False, type='bool'),
            pn_reflect=dict(required=False, type='bool'),
            pn_jumbo=dict(required=False, type='bool'),
            pn_egress_rate_limit=dict(required=False, type='str'),
            pn_eth_mode=dict(required=False, type='str',
                             choices=['1000base-x', 'sgmii',
                                      'disabled', 'GMII']),
            pn_fabric_guard=dict(required=False, type='bool'),
            pn_local_switching=dict(required=False, type='bool'),
            pn_lacp_priority=dict(required=False, type='str'),
            pn_send_port=dict(required=False, type='str'),
            pn_port_mac_address=dict(required=False, type='str'),
            pn_defer_bringup=dict(required=False, type='bool'),
        ),
        required_if=(
            ['state', 'update', ['pn_port']],
        ),
        required_one_of=[['pn_intf', 'pn_crc_check_enable', 'pn_dscp_map',
                          'pn_speed', 'pn_autoneg',
                          'pn_vxlan_termination', 'pn_pause',
                          'pn_fec', 'pn_loopback', 'pn_loop_vlans',
                          'pn_routing', 'pn_edge_switch',
                          'pn_enable', 'pn_description',
                          'pn_host_enable', 'pn_allowed_tpid',
                          'pn_mirror_only', 'pn_reflect',
                          'pn_jumbo', 'pn_egress_rate_limit',
                          'pn_eth_mode', 'pn_fabric_guard',
                          'pn_local_switching', 'pn_lacp_priority',
                          'pn_send_port', 'pn_port_mac_address',
                          'pn_defer_bringup']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    intf = module.params['pn_intf']
    crc_check_enable = module.params['pn_crc_check_enable']
    dscp_map = module.params['pn_dscp_map']
    autoneg = module.params['pn_autoneg']
    speed = module.params['pn_speed']
    port = module.params['pn_port']
    vxlan_termination = module.params['pn_vxlan_termination']
    pause = module.params['pn_pause']
    loopback = module.params['pn_loopback']
    loop_vlans = module.params['pn_loop_vlans']
    routing = module.params['pn_routing']
    edge_switch = module.params['pn_edge_switch']
    enable = module.params['pn_enable']
    description = module.params['pn_description']
    host_enable = module.params['pn_host_enable']
    allowed_tpid = module.params['pn_allowed_tpid']
    mirror_only = module.params['pn_mirror_only']
    reflect = module.params['pn_reflect']
    jumbo = module.params['pn_jumbo']
    egress_rate_limit = module.params['pn_egress_rate_limit']
    eth_mode = module.params['pn_eth_mode']
    fabric_guard = module.params['pn_fabric_guard']
    local_switching = module.params['pn_local_switching']
    lacp_priority = module.params['pn_lacp_priority']
    send_port = module.params['pn_send_port']
    port_mac_address = module.params['pn_port_mac_address']
    defer_bringup = module.params['pn_defer_bringup']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'port-config-modify':
        cli += ' %s ' % command
        if intf:
            cli += ' intf ' + intf
        if dscp_map:
            cli += ' dscp-map ' + dscp_map
        if speed:
            cli += ' speed ' + speed
        if port:
            cli += ' port ' + port
        if allowed_tpid:
            cli += ' allowed-tpid ' + allowed_tpid
        if egress_rate_limit:
            cli += ' egress-rate-limit ' + egress_rate_limit
        if eth_mode:
            cli += ' eth-mode ' + eth_mode
        if lacp_priority:
            cli += ' lacp-priority ' + lacp_priority
        if send_port:
            cli += ' send-port ' + send_port
        if port_mac_address:
            cli += ' port-mac-address ' + port_mac_address

        cli += booleanArgs(crc_check_enable, 'crc-check-enable', 'crc-check-disable')
        cli += booleanArgs(autoneg, 'autoneg', 'no-autoneg')
        cli += booleanArgs(vxlan_termination, 'vxlan-termination', 'no-vxlan-termination')
        cli += booleanArgs(pause, 'pause', 'no-pause')
        cli += booleanArgs(loopback, 'loopback', 'no-loopback')
        cli += booleanArgs(routing, 'routing', 'no-routing')
        cli += booleanArgs(edge_switch, 'edge-switch', 'no-edge-switch')
        cli += booleanArgs(enable, 'enable', 'disable')
        cli += booleanArgs(host_enable, 'host-enable', 'host-disable')
        cli += booleanArgs(mirror_only, 'mirror-only', 'no-mirror-receive-only')
        cli += booleanArgs(reflect, 'reflect', 'no-reflect')
        cli += booleanArgs(jumbo, 'jumbo', 'no-jumbo')
        cli += booleanArgs(fabric_guard, 'fabric-guard', 'no-fabric-guard')
        cli += booleanArgs(local_switching, 'local-switching', 'no-local-switching')
        cli += booleanArgs(defer_bringup, 'defer-bringup', 'no-defer-bringup')

    run_cli(module, cli)


if __name__ == '__main__':
    main()
