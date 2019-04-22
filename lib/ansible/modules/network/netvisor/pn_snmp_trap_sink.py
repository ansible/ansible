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
module: pn_snmp_trap_sink
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to create/delete snmp-trap-sink
description:
  - This module can be used to create a SNMP trap sink and delete a SNMP trap sink.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(present) to create snmp-trap-sink and
        C(absent) to delete snmp-trap-sink.
    required: true
    type: str
    choices: ['present', 'absent']
  pn_dest_host:
    description:
      - destination host.
    type: str
  pn_community:
    description:
      - community type.
    type: str
  pn_dest_port:
    description:
      - destination port.
    type: str
    default: '162'
  pn_type:
    description:
      - trap type.
    type: str
    choices: ['TRAP_TYPE_V1_TRAP', 'TRAP_TYPE_V2C_TRAP', 'TRAP_TYPE_V2_INFORM']
    default: 'TRAP_TYPE_V2C_TRAP'
"""

EXAMPLES = """
- name: snmp trap sink functionality
  pn_snmp_trap_sink:
    pn_cliswitch: "sw01"
    state: "present"
    pn_community: "foo"
    pn_type: "TRAP_TYPE_V2_INFORM"
    pn_dest_host: "192.168.67.8"

- name: snmp trap sink functionality
  pn_snmp_trap_sink:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_community: "foo"
    pn_type: "TRAP_TYPE_V2_INFORM"
    pn_dest_host: "192.168.67.8"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the snmp-trap-sink command.
  returned: always
  type: list
stderr:
  description: set of error responses from the snmp-trap-sink command.
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


def check_cli(module, cli):
    """
    This method checks for idempotency using the snmp-trap-sink-show command.
    If a trap with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    community = module.params['pn_community']
    dest_host = module.params['pn_dest_host']

    show = cli
    cli += ' snmp-community-show format community-string no-show-headers'
    rc, out, err = run_commands(module, cli)

    if out:
        out = out.split()

    if community in out:
        cli = show
        cli += ' snmp-trap-sink-show community %s format type,dest-host no-show-headers' % community
        rc, out, err = run_commands(module, cli)

        if out:
            out = out.split()

        return True if dest_host in out else False
    else:
        return None


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='snmp-trap-sink-create',
        absent='snmp-trap-sink-delete'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_dest_host=dict(required=False, type='str'),
            pn_community=dict(required=False, type='str'),
            pn_dest_port=dict(required=False, type='str', default='162'),
            pn_type=dict(required=False, type='str',
                         choices=['TRAP_TYPE_V1_TRAP',
                                  'TRAP_TYPE_V2C_TRAP',
                                  'TRAP_TYPE_V2_INFORM'],
                         default='TRAP_TYPE_V2C_TRAP'),
        ),
        required_if=(
            ["state", "present", ["pn_community", "pn_dest_host"]],
            ["state", "absent", ["pn_community", "pn_dest_host"]],
        )
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    dest_host = module.params['pn_dest_host']
    community = module.params['pn_community']
    dest_port = module.params['pn_dest_port']
    pn_type = module.params['pn_type']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    VALUE_EXISTS = check_cli(module, cli)
    cli += ' %s ' % command

    if command == 'snmp-trap-sink-create':
        if VALUE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='snmp trap sink already exists'
            )
        if VALUE_EXISTS is None:
            module.fail_json(
                failed=True,
                msg='snmp community does not exists to create trap sink'
            )
        if pn_type:
            cli += ' type ' + pn_type
        if dest_host:
            cli += ' dest-host ' + dest_host
        if community:
            cli += ' community ' + community
        if dest_port:
            cli += ' dest-port ' + dest_port

    if command == 'snmp-trap-sink-delete':
        if VALUE_EXISTS is None:
            module.fail_json(
                failed=True,
                msg='snmp community does not exists to delete trap sink'
            )
        if VALUE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='snmp-trap-sink with community %s does not exist with dest-host %s ' % (community, dest_host)
            )
        if community:
            cli += ' community ' + community
        if dest_host:
            cli += ' dest-host ' + dest_host
        if dest_port:
            cli += ' dest-port ' + dest_port

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
