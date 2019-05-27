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
module: pn_vrouter_bgp
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/modify/remove vrouter-bgp
description:
  - This module can be used to add Border Gateway Protocol neighbor to a vRouter
    modify Border Gateway Protocol neighbor to a vRouter and remove Border Gateway Protocol
    neighbor from a vRouter.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - vrouter-bgp configuration command.
    required: false
    type: str
    choices: ['present', 'absent', 'update']
    default: 'present'
  pn_neighbor:
    description:
      - IP address for BGP neighbor.
    required: true
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: true
    type: str
  pn_send_community:
    description:
      - send any community attribute to neighbor.
    required: false
    type: bool
  pn_weight:
    description:
      - default weight value between 0 and 65535 for the neighbor's routes.
    required: false
  pn_multi_protocol:
    description:
      - Multi-protocol features.
    required: false
    choices: ['ipv4-unicast', 'ipv6-unicast']
  pn_prefix_list_in:
    description:
      - prefixes used for filtering.
    required: false
    type: str
  pn_route_reflector_client:
    description:
      - set as route reflector client.
    required: false
    type: bool
  pn_default_originate:
    description:
      - announce default routes to the neighbor or not.
    required: false
    type: bool
  pn_neighbor_holdtime:
    description:
      - BGP Holdtime (seconds).
    required: false
    type: str
  pn_connect_retry_interval:
    description:
      - BGP Connect retry interval (seconds).
    required: false
    type: str
  pn_advertisement_interval:
    description:
      - Minimum interval between sending BGP routing updates.
    required: false
    type: str
  pn_route_map_out:
    description:
      - route map out for nbr.
    required: false
    type: str
  pn_update_source:
    description:
      - IP address of BGP packets required for peering over loopback interface.
    required: false
    type: str
  pn_bfd:
    description:
      - BFD protocol support for fault detection.
    required: false
    type: bool
    default: False
  pn_next_hop_self:
    description:
      - BGP next hop is self or not.
    required: false
    type: bool
  pn_allowas_in:
    description:
      - Allow/reject routes with local AS in AS_PATH.
    required: false
    type: bool
  pn_neighbor_keepalive_interval:
    description:
      - BGP Keepalive interval (seconds).
    required: false
    type: str
  pn_max_prefix:
    description:
      - maximum number of prefixes.
    required: false
    type: str
  pn_bfd_multihop:
    description:
      - always use BFD multi-hop port for fault detection.
    required: false
    type: bool
  pn_interface:
    description:
      - Interface to reach the neighbor.
    required: false
    type: str
  pn_password:
    description:
      - password for MD5 BGP.
    required: false
    type: str
  pn_route_map_in:
    description:
      - route map in for nbr.
    required: false
    type: str
  pn_soft_reconfig_inbound:
    description:
      - soft reset to reconfigure inbound traffic.
    required: false
    type: bool
  pn_override_capability:
    description:
      - override capability.
    required: false
    type: bool
  pn_max_prefix_warn_only:
    description:
      - warn if the maximum number of prefixes is exceeded.
    required: false
    type: bool
  pn_ebgp_multihop:
    description:
      - value for external BGP from 1 to 255.
    required: false
    type: str
  pn_remote_as:
    description:
      - BGP remote AS from 1 to 4294967295.
    required: false
    type: str
  pn_prefix_list_out:
    description:
      - prefixes used for filtering outgoing packets.
    required: false
    type: str
  pn_no_route_map_out:
    description:
      - Remove egress route-map from BGP neighbor.
    required: false
    type: str
  pn_no_route_map_in:
    description:
      - Remove ingress route-map from BGP neighbor.
    required: false
    type: str
"""

EXAMPLES = """
- name: "Add BGP to vRouter"
  pn_vrouter_bgp:
    state: 'present'
    pn_vrouter_name: 'sw01-vrouter'
    pn_neighbor: '105.104.104.1'
    pn_remote_as: 65000
    pn_bfd: true

- name: "Remove BGP to vRouter"
  pn_vrouter_bgp:
    state: 'absent'
    pn_vrouter_name: 'sw01-vrouter'
    pn_neighbor: '105.104.104.1'

- name: "Modify BGP to vRouter"
  pn_vrouter_bgp:
    state: 'update'
    pn_vrouter_name: 'sw01-vrouter'
    pn_neighbor: '105.104.104.1'
    pn_remote_as: 65000
    pn_bfd: false
    pn_allowas_in: true
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-bgp command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-bgp command.
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


def is_valid(module, param_name, param_val, min_val, max_val):
    if int(param_val) < min_val or int(param_val) > max_val:
        module.fail_json(
            failed=True,
            msg='Valid %s range is %s to %s' % (param_name, min_val, max_val)
        )


def check_cli(module, cli):
    """
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the vrouter-bgp-show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If the given neighbor exists on the given vRouter, return NEIGHBOR_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Booleans: VROUTER_EXISTS, NEIGHBOR_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    neighbor = module.params['pn_neighbor']

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers'
    out = run_commands(module, check_vrouter)[1]
    if out:
        out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    if neighbor:
        # Check for BGP neighbor
        show = cli + ' vrouter-bgp-show vrouter-name %s ' % vrouter_name
        show += 'format neighbor no-show-headers'
        out = run_commands(module, show)[1]

        if out and neighbor in out.split():
            NEIGHBOR_EXISTS = True
        else:
            NEIGHBOR_EXISTS = False

    return VROUTER_EXISTS, NEIGHBOR_EXISTS


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vrouter-bgp-add',
        absent='vrouter-bgp-remove',
        update='vrouter-bgp-modify'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_neighbor=dict(required=True, type='str'),
        pn_vrouter_name=dict(required=True, type='str'),
        pn_send_community=dict(required=False, type='bool'),
        pn_weight=dict(required=False, type='str'),
        pn_multi_protocol=dict(required=False, type='str', choices=['ipv4-unicast', 'ipv6-unicast']),
        pn_prefix_list_in=dict(required=False, type='str'),
        pn_route_reflector_client=dict(required=False, type='bool'),
        pn_default_originate=dict(required=False, type='bool'),
        pn_neighbor_holdtime=dict(required=False, type='str'),
        pn_connect_retry_interval=dict(required=False, type='str'),
        pn_advertisement_interval=dict(required=False, type='str'),
        pn_route_map_out=dict(required=False, type='str'),
        pn_update_source=dict(required=False, type='str'),
        pn_bfd=dict(required=False, type='bool', default=False),
        pn_next_hop_self=dict(required=False, type='bool'),
        pn_allowas_in=dict(required=False, type='bool'),
        pn_neighbor_keepalive_interval=dict(required=False, type='str'),
        pn_max_prefix=dict(required=False, type='str'),
        pn_bfd_multihop=dict(required=False, type='bool'),
        pn_interface=dict(required=False, type='str'),
        pn_password=dict(required=False, type='str', no_log=True),
        pn_route_map_in=dict(required=False, type='str'),
        pn_soft_reconfig_inbound=dict(required=False, type='bool'),
        pn_override_capability=dict(required=False, type='bool'),
        pn_max_prefix_warn_only=dict(required=False, type='bool'),
        pn_ebgp_multihop=dict(required=False, type='str'),
        pn_remote_as=dict(required=False, type='str'),
        pn_prefix_list_out=dict(required=False, type='str'),
        pn_no_route_map_out=dict(required=False, type='str'),
        pn_no_route_map_in=dict(required=False, type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ["pn_vrouter_name", "pn_neighbor", "pn_remote_as"]],
            ["state", "absent", ["pn_vrouter_name", "pn_neighbor"]],
            ["state", "update", ["pn_vrouter_name", "pn_neighbor"]]
        ),
        required_one_of=[['pn_send_community', 'pn_weight', 'pn_multi_protocol',
                          'pn_prefix_list_in', 'pn_route_reflector_client', 'pn_default_originate',
                          'pn_neighbor_holdtime', 'pn_connect_retry_interval', 'pn_advertisement_interval',
                          'pn_route_map_out', 'pn_update_source', 'pn_bfd',
                          'pn_next_hop_self', 'pn_allowas_in', 'pn_neighbor_keepalive_interval',
                          'pn_max_prefix', 'pn_bfd_multihop', 'pn_interface',
                          'pn_password', 'pn_route_map_in', 'pn_soft_reconfig_inbound',
                          'pn_override_capability', 'pn_max_prefix_warn_only', 'pn_ebgp_multihop',
                          'pn_remote_as', 'pn_prefix_list_out', 'pn_no_route_map_out',
                          'pn_no_route_map_in']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    neighbor = module.params['pn_neighbor']
    vrouter_name = module.params['pn_vrouter_name']
    send_community = module.params['pn_send_community']
    weight = module.params['pn_weight']
    multi_protocol = module.params['pn_multi_protocol']
    prefix_list_in = module.params['pn_prefix_list_in']
    route_reflector_client = module.params['pn_route_reflector_client']
    default_originate = module.params['pn_default_originate']
    neighbor_holdtime = module.params['pn_neighbor_holdtime']
    connect_retry_interval = module.params['pn_connect_retry_interval']
    advertisement_interval = module.params['pn_advertisement_interval']
    route_map_out = module.params['pn_route_map_out']
    update_source = module.params['pn_update_source']
    bfd = module.params['pn_bfd']
    next_hop_self = module.params['pn_next_hop_self']
    allowas_in = module.params['pn_allowas_in']
    neighbor_keepalive_interval = module.params['pn_neighbor_keepalive_interval']
    max_prefix = module.params['pn_max_prefix']
    bfd_multihop = module.params['pn_bfd_multihop']
    interface = module.params['pn_interface']
    password = module.params['pn_password']
    route_map_in = module.params['pn_route_map_in']
    soft_reconfig_inbound = module.params['pn_soft_reconfig_inbound']
    override_capability = module.params['pn_override_capability']
    max_prefix_warn_only = module.params['pn_max_prefix_warn_only']
    ebgp_multihop = module.params['pn_ebgp_multihop']
    remote_as = module.params['pn_remote_as']
    prefix_list_out = module.params['pn_prefix_list_out']
    no_route_map_out = module.params['pn_no_route_map_out']
    no_route_map_in = module.params['pn_no_route_map_in']

    command = state_map[state]

    if weight and weight != 'none':
        if int(weight) < 1 or int(weight) > 65535:
            module.fail_json(
                failed=True,
                msg='Valid weight range is 1 to 65535'
            )

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)
    VROUTER_EXISTS, NEIGHBOR_EXISTS = check_cli(module, cli)

    if state:
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )

    if command == 'vrouter-bgp-remove' or command == 'vrouter-bgp-modify':
        if NEIGHBOR_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='BGP neighbor with IP %s does not exist on %s' % (neighbor, vrouter_name)
            )

    if command == 'vrouter-bgp-add':
        if NEIGHBOR_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='BGP neighbor with IP %s already exists on %s' % (neighbor, vrouter_name)
            )

    cli += ' %s vrouter-name %s neighbor %s ' % (command, vrouter_name, neighbor)

    if command == 'vrouter-bgp-add' or command == 'vrouter-bgp-modify':
        if weight:
            cli += ' weight ' + weight
        if multi_protocol:
            cli += ' multi-protocol ' + multi_protocol
        if prefix_list_in:
            cli += ' prefix-list-in ' + prefix_list_in
        if neighbor_holdtime:
            is_valid(module, 'neighbor holdtime', neighbor_holdtime, '0', '65535')
            cli += ' neighbor-holdtime ' + neighbor_holdtime
        if connect_retry_interval:
            is_valid(module, 'connect retry interval', connect_retry_interval, '0', '65535')
            cli += ' connect-retry-interval ' + connect_retry_interval
        if advertisement_interval:
            is_valid(module, 'advertisement interval', advertisement_interval, '0', '65535')
            cli += ' advertisement-interval ' + advertisement_interval
        if route_map_out:
            cli += ' route-map-out ' + route_map_out
        if update_source:
            cli += ' update-source ' + update_source
        if neighbor_keepalive_interval:
            is_valid(module, 'neighbor keepalive interval', neighbor_keepalive_interval, '0', '65535')
            cli += ' neighbor-keepalive-interval ' + neighbor_keepalive_interval
        if max_prefix:
            cli += ' max-prefix ' + max_prefix
        if interface:
            cli += ' interface ' + interface
        if password:
            cli += ' password ' + password
        if route_map_in:
            cli += ' route-map-in ' + route_map_in
        if ebgp_multihop:
            is_valid(module, 'ebgp_multihop', ebgp_multihop, '1', '255')
            cli += ' ebgp-multihop ' + ebgp_multihop
        if remote_as:
            cli += ' remote-as ' + remote_as
        if prefix_list_out:
            cli += ' prefix-list-out ' + prefix_list_out
        cli += booleanArgs(send_community, 'send-community', 'no-send-community')
        cli += booleanArgs(route_reflector_client, 'route-reflector-client', 'no-route-reflector-client')
        cli += booleanArgs(default_originate, 'default-originate', 'no-default-originate')
        cli += booleanArgs(bfd, 'bfd', 'no-bfd')
        cli += booleanArgs(next_hop_self, 'next-hop-self', 'no-next-hop-self')
        cli += booleanArgs(allowas_in, 'allowas-in', 'no-allowas-in')
        cli += booleanArgs(bfd_multihop, 'bfd-multihop', 'no-bfd-multihop')
        cli += booleanArgs(soft_reconfig_inbound, 'soft-reconfig-inbound', 'no-soft-reconfig-inbound')
        cli += booleanArgs(override_capability, 'override-capability', 'no-override-capability')
        cli += booleanArgs(max_prefix_warn_only, 'max-prefix-warn-only', 'no-max-prefix-warn-only')

    if command == 'vrouter-bgp-modify':
        if no_route_map_out:
            cli += ' no-route-map-out ' + no_route_map_out
        if no_route_map_in:
            cli += ' no-route-map-in ' + no_route_map_in

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
