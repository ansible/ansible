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
module: pn_port_config
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: 2.8
short_description: CLI command to modify port-config
description:
  - This module can be used to modify a port configuration.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the port-config.
    required: True
    type: str
    choices: ['update']
  pn_intf:
    description:
      - physical interface.
    required: False
    type: str
  pn_crc_check_enable:
    description:
      - CRC check on ingress and rewrite on egress.
    required: False
    type: bool
  pn_dscp_map:
    description:
      - DSCP map name to enable on port.
    required: False
    type: str
  pn_autoneg:
    description:
      - physical port autonegotiation.
    required: False
    type: bool
  pn_speed:
    description:
      - physical port speed.
    required: False
    choices: ['disable', '10m', '100m', '1g',
              '2.5g', '10g', '25g', '40g', '50g', '100g']
  pn_port:
    description:
      - physical port.
    required: False
    type: str
  pn_vxlan_termination:
    description:
      - physical port vxlan termination setting.
    required: False
    type: bool
  pn_pause:
    description:
      - physical port pause.
    required: False
    type: bool
  pn_loopback:
    description:
      - physical port loopback.
    required: False
    type: bool
  pn_loop_vlans:
    description:
      - looping vlans.
    required: False
    type: str
  pn_routing:
    description:
      - routing.
    required: False
    type: bool
  pn_edge_switch:
    description:
      - physical port edge switch.
    required: False
    type: bool
  pn_enable:
    description:
      - physical port enable.
    required: False
    type: bool
  pn_description:
    description:
      - physical port description.
    required: False
    type: str
  pn_host_enable:
    description:
      - Host facing port control setting.
    required: False
    type: bool
  pn_allowed_tpid:
    description:
      - Allowed TPID in addition to 0x8100 on Vlan header.
    required: False
    type: str
    choices: ['vlan', 'q-in-q', 'q-in-q-old']
  pn_mirror_only:
    description:
      - physical port mirror only.
    required: False
    type: bool
  pn_reflect:
    description:
      - physical port reflection.
    required: False
    type: bool
  pn_jumbo:
    description:
      - jumbo frames on physical port.
    required: False
    type: bool
  pn_egress_rate_limit:
    description:
      - max egress port data rate limit.
    required: False
    type: str
  pn_eth_mode:
    description:
      - physical Ethernet mode.
    required: False
    choices: ['1000base-x', 'sgmii', 'disabled', 'GMII']
  pn_fabric_guard:
    description:
      - Fabric guard configuration.
    required: False
    type: bool
  pn_local_switching:
    description:
      - no-local-switching port cannot bridge traffic to
        another no-local-switching port.
    required: False
    type: bool
  pn_lacp_priority:
    description:
      - LACP priority from 1 to 65535.
    required: False
    type: str
  pn_send_port:
    description:
      - send port.
    required: False
    type: str
  pn_port_mac_address:
    description:
      - physical port MAC Address.
    required: False
    type: str
  pn_defer_bringup:
    description:
      - defer port bringup.
    required: False
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
    pn_host_enable: true
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module, cli):
    """
    This method checks for idempotency using the dscp-map-show name command.
    If a user with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_dscp_map']

    cli += ' dscp-map-show name %s format name no-show-headers' % name
    out = run_commands(module, cli)[1]

    out = out.split()

    return True if name in out[-1] else False


def main():
    """ This section is for arguments parsing """

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

    if dscp_map:
        NAME_EXISTS = check_cli(module, cli)

    if command == 'port-config-modify':
        cli += ' %s ' % command
        if dscp_map:
            if NAME_EXISTS is False:
                module.fail_json(
                    failed=True,
                    msg='Create dscp map with name %s before updating' % dscp_map
                )

            cli += ' dscp-map ' + dscp_map
        if intf:
            cli += ' intf ' + intf
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

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
