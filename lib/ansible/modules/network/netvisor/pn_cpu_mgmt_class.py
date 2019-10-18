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
module: pn_cpu_mgmt_class
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: 2.8
short_description: CLI command to modify cpu-mgmt-class
description:
  - This module can we used to update mgmt port ingress policers.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    type: str
    required: false
  state:
    description:
      - State the action to perform. Use C(update) to modify cpu-mgmt-class.
    type: str
    required: true
    choices: ['update']
  pn_burst_size:
    description:
      - ingress traffic burst size (bytes) or default.
    required: false
    type: str
  pn_name:
    description:
      - mgmt port ingress traffic class.
    type: str
    required: false
    choices: ['arp', 'icmp', 'ssh', 'snmp', 'fabric', 'bcast', 'nfs',
              'web', 'web-ssl', 'net-api']
  pn_rate_limit:
    description:
      - ingress rate limit on mgmt port(bps) or unlimited.
    type: str
    required: false
"""

EXAMPLES = """
- name: cpu mgmt class modify ingress policers
  pn_cpu_mgmt_class:
    pn_cliswitch: "sw01"
    state: "update"
    pn_name: "icmp"
    pn_rate_limit: "10000"
    pn_burst_size: "14000"

- name: cpu mgmt class modify ingress policers
  pn_cpu_mgmt_class:
    pn_cliswitch: "sw01"
    state: "update"
    pn_name: "snmp"
    pn_burst_size: "8000"
    pn_rate_limit: "100000"

- name: cpu mgmt class modify ingress policers
  pn_cpu_mgmt_class:
    pn_cliswitch: "sw01"
    state: "update"
    pn_name: "web"
    pn_rate_limit: "10000"
    pn_burst_size: "1000"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the cpu-mgmt-class command.
  returned: always
  type: list
stderr:
  description: set of error responses from the cpu-mgmt-class command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='cpu-mgmt-class-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str', choices=state_map.keys()),
            pn_burst_size=dict(required=False, type='str'),
            pn_name=dict(required=False, type='str',
                         choices=['arp', 'icmp', 'ssh', 'snmp',
                                  'fabric', 'bcast', 'nfs', 'web',
                                  'web-ssl', 'net-api']),
            pn_rate_limit=dict(required=False, type='str'),
        ),
        required_if=([['state', 'update', ['pn_name', 'pn_burst_size', 'pn_rate_limit']]]),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    burst_size = module.params['pn_burst_size']
    name = module.params['pn_name']
    rate_limit = module.params['pn_rate_limit']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'cpu-mgmt-class-modify':
        cli += ' %s name %s ' % (command, name)
        cli += ' burst-size %s rate-limit %s' % (burst_size, rate_limit)

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
