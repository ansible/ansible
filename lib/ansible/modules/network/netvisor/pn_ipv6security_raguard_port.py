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
module: pn_ipv6security_raguard_port
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/remove ipv6security-raguard-port
description:
  - This module can be used to add ports to RA Guard Policy and remove ports to RA Guard Policy.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - ipv6security-raguard-port configuration command.
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  pn_name:
    description:
      - RA Guard Policy Name.
    required: true
    type: str
  pn_ports:
    description:
      - Ports attached to RA Guard Policy.
    required: true
    type: str
"""

EXAMPLES = """
- name: ipv6 security raguard port add
  pn_ipv6security_raguard_port:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    pn_ports: "1"

- name: ipv6 security raguard port remove
  pn_ipv6security_raguard_port:
    pn_cliswitch: "sw01"
    pn_name: "foo"
    state: "absent"
    pn_ports: "1"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the ipv6security-raguard-port command.
  returned: always
  type: list
stderr:
  description: set of error responses from the ipv6security-raguard-port command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, run_cli
from ansible.module_utils.network.netvisor.netvisor import run_commands


def check_cli(module):
    """
    This method checks for idempotency using the ipv6security-raguard-show command.
    If a name exists, return True if name exists else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_name']

    cli = 'ipv6security-raguard-show format name parsable-delim ,'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='ipv6security-raguard-port-add',
        absent='ipv6security-raguard-port-remove'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_name=dict(required=True, type='str'),
        pn_ports=dict(required=True, type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    name = module.params['pn_name']
    ports = module.params['pn_ports']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module)

    if command:
        if NAME_EXISTS is False:
            module.fail_json(
                failed=True,
                msg='ipv6 security raguard with name %s does not exist to add ports' % name
            )

    cli += ' %s name %s ports %s' % (command, name, ports)

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
