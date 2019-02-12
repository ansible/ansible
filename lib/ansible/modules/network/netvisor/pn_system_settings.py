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
module: pn_system_settings
author: "Pluribus Networks (@rajaspachipulusu17)"
version: "2.8"
short_description: CLI command to modify system-settings
description:
  - This module can be used to update system settings.
options:
  pn_cliusername:
    description:
      - Provide login username.
    required: false
    type: str
  pn_clipassword:
    description:
      - Provide login password.
    required: false
    type: str
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. C(update) to modify system-settings.
    required: true
    type: str
    choices: ['update']
  pn_optimize_arps:
    description:
      - enable ARP optimization.
    required: false
    type: bool
  pn_reactivate_mac:
    description:
      - enable reactivation of aged out mac entries.
    required: false
    type: bool
  pn_pfc_buffer_limit:
    description:
      - percentae of maximum buffers allowed for PFC.
    required: false
    type: str
  pn_optimize_datapath:
    description:
      - Datapath optimization for cluster, fabric and data communication.
    required: false
    type: str
    choices: ['disable', 'cluster-only', 'all']
  pn_lldp:
    description:
      - LLDP.
    required: false
    type: bool
  pn_vle_tracking_timeout:
    description:
      - vle tracking timeout.
    required: false
    type: str
  pn_block_loops:
    description:
      - enable loop blocking.
    required: false
    type: bool
  pn_routing_over_vlags:
    description:
      - enable/disable routing to vlags from cluster links.
    required: false
    type: bool
  pn_lossless_mode:
    description:
      - switch lossless mode.
    required: false
    type: bool
  pn_proxy_conn_retry_interval:
    description:
      - milliseconds to wait between proxy connection retry attempt.
    required: false
    type: str
  pn_proxy_conn_retry:
    description:
      - Enable/Disable proxy connection retry.
    required: false
    type: bool
  pn_cluster_active_active_routing:
    description:
      - active-active routing on a cluster.
    required: false
    type: bool
  pn_reactivate_vxlan_tunnel_mac:
    description:
      - enable reactivation of mac entries over vxlan tunnels.
    required: false
    type: bool
  pn_cpu_class_enable:
    description:
      - cpu class enable.
    required: false
    type: bool
  pn_use_igmp_snoop_l2:
    description:
      - Use L2/L3 tables for IGMP Snooping.
    required: false
    type: bool
  pn_host_refresh:
    description:
      - enable refreshing host arp entries to keep l2 entries active.
    required: false
    type: bool
  pn_auto_host_bundle:
    description:
      - enable auto host bundling.
    required: false
    type: bool
  pn_stagger_queries:
    description:
      - Stagger igmp/mld snooping Queries.
    required: false
    type: bool
  pn_usb_port:
    description:
      - usb port.
    required: false
    type: bool
  pn_policy_based_routing:
    description:
      - enable policy based routing.
    required: false
    type: bool
  pn_manage_unknown_unicast:
    description:
      - enable unknown unicast management.
    required: false
    type: bool
  pn_optimize_nd:
    description:
      - enable ND optimization.
    required: false
    type: bool
  pn_manage_broadcast:
    description:
      - enable broadcast management.
    required: false
    type: bool
  pn_source_mac_miss:
    description:
      - control unknown source mac learn behavior.
    required: false
    type: str
    choices: ['to-cpu', 'copy-to-cpu']
  pn_cosq_weight_auto:
    description:
      - Adjust queue weights automatically based on min-guarantee configuration.
    required: false
    type: bool
  pn_auto_trunk:
    description:
      - enable auto trunking.
    required: false
    type: bool
  pn_proxy_conn_max_retry:
    description:
      - Maximum number of proxy connection retry attempt.
    required: false
    type: str
"""

EXAMPLES = """
- name: Modify system settings
  pn_system_settings:
    pn_cliusername: "foo"
    pn_clipassword: "foo123"
    pn_cliswitch: "sw01"
    state: "update"
    pn_policy_based_routing: True

- name: Modify system settings
  pn_system_settings:
    pn_cliusername: "foo"
    pn_clipassword: "foo123"
    pn_cliswitch: "sw01"
    state: "update"
    pn_auto_trunk: False
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the system-settings command.
  returned: always
  type: list
stderr:
  description: set of error responses from the system-settings command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs


RESTART_STR = "nvOSd must be restarted for this setting to take effect"


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='system-settings-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str', no_log=True),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_optimize_arps=dict(required=False, type='bool'),
            pn_reactivate_mac=dict(required=False, type='bool'),
            pn_pfc_buffer_limit=dict(required=False, type='str'),
            pn_optimize_datapath=dict(required=False, type='str',
                                      choices=['disable', 'cluster-only',
                                               'all']),
            pn_lldp=dict(required=False, type='bool'),
            pn_vle_tracking_timeout=dict(required=False, type='str'),
            pn_block_loops=dict(required=False, type='bool'),
            pn_routing_over_vlags=dict(required=False, type='bool'),
            pn_lossless_mode=dict(required=False, type='bool'),
            pn_proxy_conn_retry_interval=dict(required=False, type='str'),
            pn_proxy_conn_retry=dict(required=False, type='bool'),
            pn_cluster_active_active_routing=dict(required=False, type='bool'),
            pn_reactivate_vxlan_tunnel_mac=dict(required=False, type='bool'),
            pn_cpu_class_enable=dict(required=False, type='bool'),
            pn_use_igmp_snoop_l2=dict(required=False, type='bool'),
            pn_host_refresh=dict(required=False, type='bool'),
            pn_auto_host_bundle=dict(required=False, type='bool'),
            pn_stagger_queries=dict(required=False, type='bool'),
            pn_usb_port=dict(required=False, type='bool'),
            pn_policy_based_routing=dict(required=False, type='bool'),
            pn_manage_unknown_unicast=dict(required=False, type='bool'),
            pn_optimize_nd=dict(required=False, type='bool'),
            pn_manage_broadcast=dict(required=False, type='bool'),
            pn_source_mac_miss=dict(required=False, type='str',
                                    choices=['to-cpu', 'copy-to-cpu']),
            pn_cosq_weight_auto=dict(required=False, type='bool'),
            pn_auto_trunk=dict(required=False, type='bool'),
            pn_proxy_conn_max_retry=dict(required=False, type='str'),
        ),
        required_one_of=[['pn_optimize_arps', 'pn_reactivate_mac',
                          'pn_pfc_buffer_limit', 'pn_optimize_datapath',
                          'pn_lldp', 'pn_vle_tracking_timeout',
                          'pn_block_loops', 'pn_routing_over_vlags',
                          'pn_lossless_mode', 'pn_proxy_conn_retry_interval',
                          'pn_proxy_conn_retry', 'pn_cpu_class_enable',
                          'pn_cluster_active_active_routing', 'pn_host_refresh',
                          'pn_reactivate_vxlan_tunnel_mac', 'pn_auto_trunk',
                          'pn_use_igmp_snoop_l2', 'pn_host_refresh',
                          'pn_auto_host_bundle', 'pn_stagger_queries',
                          'pn_usb_port', 'pn_policy_based_routing',
                          'pn_manage_unknown_unicast', 'pn_optimize_nd',
                          'pn_manage_broadcast', 'pn_source_mac_miss',
                          'pn_cosq_weight_auto', 'pn_cosq_weight_auto',
                          'pn_proxy_conn_max_retry']],
    )

    # Accessing the arguments
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    optimize_arps = module.params['pn_optimize_arps']
    reactivate_mac = module.params['pn_reactivate_mac']
    pfc_buffer_limit = module.params['pn_pfc_buffer_limit']
    optimize_datapath = module.params['pn_optimize_datapath']
    lldp = module.params['pn_lldp']
    vle_tracking_timeout = module.params['pn_vle_tracking_timeout']
    block_loops = module.params['pn_block_loops']
    routing_over_vlags = module.params['pn_routing_over_vlags']
    lossless_mode = module.params['pn_lossless_mode']
    proxy_conn_retry_interval = module.params['pn_proxy_conn_retry_interval']
    proxy_conn_retry = module.params['pn_proxy_conn_retry']
    cluster_active_active_routing = module.params['pn_cluster_active_active_routing']
    reactivate_vxlan_tunnel_mac = module.params['pn_reactivate_vxlan_tunnel_mac']
    cpu_class_enable = module.params['pn_cpu_class_enable']
    use_igmp_snoop_l2 = module.params['pn_use_igmp_snoop_l2']
    host_refresh = module.params['pn_host_refresh']
    auto_host_bundle = module.params['pn_auto_host_bundle']
    stagger_queries = module.params['pn_stagger_queries']
    usb_port = module.params['pn_usb_port']
    policy_based_routing = module.params['pn_policy_based_routing']
    manage_unknown_unicast = module.params['pn_manage_unknown_unicast']
    optimize_nd = module.params['pn_optimize_nd']
    manage_broadcast = module.params['pn_manage_broadcast']
    source_mac_miss = module.params['pn_source_mac_miss']
    cosq_weight_auto = module.params['pn_cosq_weight_auto']
    auto_trunk = module.params['pn_auto_trunk']
    proxy_conn_max_retry = module.params['pn_proxy_conn_max_retry']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch, username, password)

    if command == 'system-settings-modify':
        cli += ' %s ' % command

        cli += booleanArgs(optimize_arps, 'optimize-arps', 'no-optimize-arps')
        cli += booleanArgs(reactivate_mac, 'reactivate-mac', 'no-reactivate-mac')
        cli += booleanArgs(lldp, 'lldp', 'no-lldp')
        cli += booleanArgs(block_loops, 'block-loops', 'no-block-loops')
        cli += booleanArgs(routing_over_vlags, 'routing-over-vlags', 'no-routing-over-vlags')
        cli += booleanArgs(lossless_mode, 'lossless-mode', 'no-lossless-mode')
        cli += booleanArgs(proxy_conn_retry, 'proxy-conn-retry', 'no-proxy-conn-retry')
        cli += booleanArgs(cluster_active_active_routing, 'cluster-active-active-routing', 'no-cluster-active-active-routing')
        cli += booleanArgs(reactivate_vxlan_tunnel_mac, 'reactivate-vxlan-tunnel-mac', 'no-cluster-active-active-routing')
        cli += booleanArgs(cpu_class_enable, 'cpu-class-enable', 'no-cpu-class-enable')
        cli += booleanArgs(use_igmp_snoop_l2, 'use-igmp-snoop-l2', 'use-igmp-snoop-l3')
        cli += booleanArgs(host_refresh, 'host-refresh', 'no-host-refresh')
        cli += booleanArgs(auto_host_bundle, 'auto-host-bundle', 'no-auto-host-bundle')
        cli += booleanArgs(stagger_queries, 'stagger-queries', 'no-stagger-queries')
        cli += booleanArgs(usb_port, 'usb-port', 'no-usb-port')
        cli += booleanArgs(policy_based_routing, 'policy-based-routing', 'no-policy-based-routing')
        cli += booleanArgs(manage_unknown_unicast, 'manage-unknown-unicast', 'no-manage-unknown-unicast')
        cli += booleanArgs(optimize_nd, 'optimize-nd', 'no-optimize-nd')
        cli += booleanArgs(manage_broadcast, 'manage-broadcast', 'no-manage-broadcast')
        cli += booleanArgs(cosq_weight_auto, 'cosq-weight-auto', 'no-cosq-weight-auto')
        cli += booleanArgs(auto_trunk, 'auto-trunk', 'no-auto-trunk')

        if pfc_buffer_limit:
            cli += ' pfc-buffer-limit ' + pfc_buffer_limit
        if optimize_datapath:
            cli += ' optimize-datapath ' + optimize_datapath
        if vle_tracking_timeout:
            cli += ' vle-tracking-timeout ' + vle_tracking_timeout
        if proxy_conn_retry_interval:
            cli += ' proxy-conn-retry-interval ' + proxy_conn_retry_interval
        if source_mac_miss:
            cli += ' source-mac-miss ' + source_mac_miss
        if proxy_conn_max_retry:
            cli += ' proxy-conn-max-retry ' + proxy_conn_max_retry

    aggr_cli = cli
    out = run_cli(module, cli, state_map)
    aggr_out = out

    if out is not None:
        if RESTART_STR in out:
            cli = pn_cli(module, switch, username, password)
            cli += ' switch-reboot '
            aggr_cli += ' and ' + cli
            out = run_cli(module, cli, state_map)
            if out is not None:
                aggr_out += out
        module.exit_json(
            command=aggr_cli,
            stdout=aggr_out.strip(),
            msg="system-settings %s operation completed" % action,
            changed=True
        )
    else:
        module.exit_json(
            command=aggr_cli,
            stdout=aggr_out.strip(),
            msg="system-settings %s operation completed" % action,
            changed=True
        )


if __name__ == '__main__':
    main()
