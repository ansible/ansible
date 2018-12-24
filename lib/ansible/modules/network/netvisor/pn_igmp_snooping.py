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
module: pn_igmp_snooping
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify igmp-snooping
description:
  - This module can be used to modify Internet Group Management Protocol (IGMP) snooping.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the igmp-snooping.
    required: True
    type: str
    choices: ['update']
  pn_enable:
    description:
      - enable or disable IGMP snooping.
    required: False
    type: bool
  pn_query_interval:
    description:
      - IGMP query interval in seconds.
    required: False
    type: str
  pn_igmpv2_vlans:
    description:
      - VLANs on which to use IGMPv2 protocol.
    required: False
    type: str
  pn_igmpv3_vlans:
    description:
      - VLANs on which to use IGMPv3 protocol.
    required: False
    type: str
  pn_enable_vlans:
    description:
      - enable per VLAN IGMP snooping.
    required: False
    type: str
  pn_vxlan:
    description:
      - enable or disable IGMP snooping on vxlans.
    required: False
    type: bool
  pn_query_max_response_time:
    description:
      - maximum response time, in seconds, advertised in IGMP queries.
    required: False
    type: str
  pn_scope:
    description:
      - IGMP snooping scope - fabric or local.
    required: False
    choices: ['local', 'fabric']
  pn_no_snoop_linklocal_vlans:
    description:
      - Remove snooping of link-local groups(224.0.0.0/24) on these vlans.
    required: False
    type: str
  pn_snoop_linklocal_vlans:
    description:
      - Allow snooping of link-local groups(224.0.0.0/24) on these vlans.
    required: False
    type: str
"""

EXAMPLES = """
- name: 'Modify IGMP Snooping'
  pn_igmp_snooping:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_vxlan: True
    pn_enable_vlans: '1-399,401-4092'
    pn_no_snoop_linklocal_vlans: 'none'
    pn_igmpv3_vlans: '1-399,401-4092'

- name: 'Modify IGMP Snooping'
  pn_igmp_snooping:
    pn_cliswitch: 'sw01'
    state: 'update'
    pn_vxlan: False
    pn_enable_vlans: '1-399'
    pn_no_snoop_linklocal_vlans: 'none'
    pn_igmpv3_vlans: '1-399'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the igmp-snooping command.
  returned: always
  type: list
stderr:
  description: set of error responses from the igmp-snooping command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli, booleanArgs


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='igmp-snooping-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_enable=dict(required=False, type='bool'),
            pn_query_interval=dict(required=False, type='str'),
            pn_igmpv2_vlans=dict(required=False, type='str'),
            pn_igmpv3_vlans=dict(required=False, type='str'),
            pn_enable_vlans=dict(required=False, type='str'),
            pn_vxlan=dict(required=False, type='bool'),
            pn_query_max_response_time=dict(required=False, type='str'),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_no_snoop_linklocal_vlans=dict(required=False, type='str'),
            pn_snoop_linklocal_vlans=dict(required=False, type='str'),
        ),
        required_one_of=[['pn_enable', 'pn_query_interval',
                          'pn_igmpv2_vlans',
                          'pn_igmpv3_vlans',
                          'pn_enable_vlans',
                          'pn_vxlan',
                          'pn_query_max_response_time',
                          'pn_scope',
                          'pn_no_snoop_linklocal_vlans',
                          'pn_snoop_linklocal_vlans']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    enable = module.params['pn_enable']
    query_interval = module.params['pn_query_interval']
    igmpv2_vlans = module.params['pn_igmpv2_vlans']
    igmpv3_vlans = module.params['pn_igmpv3_vlans']
    enable_vlans = module.params['pn_enable_vlans']
    vxlan = module.params['pn_vxlan']
    query_max_response_time = module.params['pn_query_max_response_time']
    scope = module.params['pn_scope']
    no_snoop_linklocal_vlans = module.params['pn_no_snoop_linklocal_vlans']
    snoop_linklocal_vlans = module.params['pn_snoop_linklocal_vlans']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'igmp-snooping-modify':
        cli += ' %s ' % command

        cli += booleanArgs(enable, 'enable', 'disable')
        cli += booleanArgs(vxlan, 'vxlan', 'no-vxlan')

        if query_interval:
            cli += ' query-interval ' + query_interval
        if igmpv2_vlans:
            cli += ' igmpv2-vlans ' + igmpv2_vlans
        if igmpv3_vlans:
            cli += ' igmpv3-vlans ' + igmpv3_vlans
        if enable_vlans:
            cli += ' enable-vlans ' + enable_vlans
        if query_max_response_time:
            cli += ' query-max-response-time ' + query_max_response_time
        if scope:
            cli += ' scope ' + scope
        if no_snoop_linklocal_vlans:
            cli += ' no-snoop-linklocal-vlans ' + no_snoop_linklocal_vlans
        if snoop_linklocal_vlans:
            cli += ' snoop-linklocal-vlans ' + snoop_linklocal_vlans

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
