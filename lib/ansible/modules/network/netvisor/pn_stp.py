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
module: pn_stp
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify stp
description:
  - This module can be used to modify Spanning Tree Protocol parameters.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    type: str
    required: false
  state:
    description:
      - State the action to perform. Use C(update) to stp.
    type: str
    required: true
    choices: ['update']
  pn_hello_time:
    description:
      - STP hello time between 1 and 10 secs.
    type: str
    default: '2'
  pn_enable:
    description:
      - enable or disable STP
    type: bool
  pn_root_guard_wait_time:
    description:
      - root guard wait time between 0 and 300 secs. 0 to disable wait.
    type: str
    default: '20'
  pn_bpdus_bridge_ports:
    description:
      - BPDU packets to bridge specific port.
    type: bool
  pn_mst_max_hops:
    description:
      - maximum hop count for mstp bpdu.
    type: str
    default: '20'
  pn_bridge_id:
    description:
      - STP bridge id.
    type: str
  pn_max_age:
    description:
      - maximum age time between 6 and 40 secs.
    type: str
    default: '20'
  pn_stp_mode:
    description:
      - STP mode.
    type: str
    choices: ['rstp', 'mstp']
  pn_mst_config_name:
    description:
      - Name for MST Configuration Instance.
    type: str
  pn_forwarding_delay:
    description:
      - STP forwarding delay between 4 and 30 secs.
    type: str
    default: '15'
  pn_bridge_priority:
    description:
      - STP bridge priority.
    type: str
    default: '32768'
"""

EXAMPLES = """
- name: Modify stp
  pn_stp:
    pn_cliswitch: "sw01"
    state: "update"
    pn_hello_time: "3"
    pn_stp_mode: "rstp"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the stp command.
  returned: always
  type: list
stderr:
  description: set of error responses from the stp command.
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
        update='stp-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_hello_time=dict(required=False, type='str', default='2'),
            pn_enable=dict(required=False, type='bool'),
            pn_root_guard_wait_time=dict(required=False, type='str', default='20'),
            pn_bpdus_bridge_ports=dict(required=False, type='bool'),
            pn_mst_max_hops=dict(required=False, type='str', default='20'),
            pn_bridge_id=dict(required=False, type='str'),
            pn_max_age=dict(required=False, type='str', default='20'),
            pn_stp_mode=dict(required=False, type='str',
                             choices=['rstp', 'mstp']),
            pn_mst_config_name=dict(required=False, type='str'),
            pn_forwarding_delay=dict(required=False, type='str', default='15'),
            pn_bridge_priority=dict(required=False, type='str', default='32768'),
        ),
        required_one_of=[['pn_enable', 'pn_hello_time',
                          'pn_root_guard_wait_time',
                          'pn_bpdus_bridge_ports',
                          'pn_mst_max_hops',
                          'pn_bridge_id',
                          'pn_max_age',
                          'pn_stp_mode',
                          'pn_mst_config_name',
                          'pn_forwarding_delay',
                          'pn_bridge_priority']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    hello_time = module.params['pn_hello_time']
    enable = module.params['pn_enable']
    root_guard_wait_time = module.params['pn_root_guard_wait_time']
    bpdus_bridge_ports = module.params['pn_bpdus_bridge_ports']
    mst_max_hops = module.params['pn_mst_max_hops']
    bridge_id = module.params['pn_bridge_id']
    max_age = module.params['pn_max_age']
    stp_mode = module.params['pn_stp_mode']
    mst_config_name = module.params['pn_mst_config_name']
    forwarding_delay = module.params['pn_forwarding_delay']
    bridge_priority = module.params['pn_bridge_priority']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'stp-modify':
        cli += ' %s ' % command
        if hello_time:
            cli += ' hello-time ' + hello_time
        if root_guard_wait_time:
            cli += ' root-guard-wait-time ' + root_guard_wait_time
        if mst_max_hops:
            cli += ' mst-max-hops ' + mst_max_hops
        if bridge_id:
            cli += ' bridge-id ' + bridge_id
        if max_age:
            cli += ' max-age ' + max_age
        if stp_mode:
            cli += ' stp-mode ' + stp_mode
        if mst_config_name:
            cli += ' mst-config-name ' + mst_config_name
        if forwarding_delay:
            cli += ' forwarding-delay ' + forwarding_delay
        if bridge_priority:
            cli += ' bridge-priority ' + bridge_priority

        cli += booleanArgs(enable, 'enable', 'disable')
        cli += booleanArgs(bpdus_bridge_ports, 'bpdus-bridge-ports', 'bpdus-all-ports')

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
