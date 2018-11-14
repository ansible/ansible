#!/usr/bin/python
""" PN CLI snmp-trap-sink-create/delete """
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
module: pn_snmp_trap_sink
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to create/delete snmp-trap-sink.
description:
  - C(create): create a SNMP trap sink
  - C(delete): delete a SNMP trap sink
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
  state:
    description:
      - State the action to perform. Use 'present' to create snmp-trap-sink and
        'absent' to delete snmp-trap-sink.
    required: True
  pn_dest_host:
    description:
      - destination host
    type: str
  pn_community:
    description:
      - community type
    type: str
  pn_dest_port:
    description:
      - destination port - default 162
    type: str
  pn_type:
    description:
      - trap type - default TRAP_TYPE_V2C_TRAP
    choices: ['TRAP_TYPE_V1_TRAP', 'TRAP_TYPE_V2C_TRAP', 'TRAP_TYPE_V2_INFORM']
"""

EXAMPLES = """
- name: snmp trap sink functionality
  pn_snmp_trap_sink:
    pn_cliswitch: "sw01"
    state: "present"
    pn_community: "F4u1tMgmt"
    pn_type: "TRAP_TYPE_V2_INFORM"
    pn_dest_host: "192.168.67.8"

- name: snmp trap sink functionality
  pn_snmp_trap_sink:
    pn_cliswitch: "sw01"
    state: "absent"
    pn_community: "F4u1tMgmt"
    pn_type: "TRAP_TYPE_V2_INFORM"
    pn_dest_host: "192.168.67.8"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
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


import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli


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
            ["state", "absent", ["pn_community", "pn_dest_host", "pn_type"]],
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

    check_cli(module, cli)
    cli += ' %s ' % command

    if command == 'snmp-trap-sink-create':
        if pn_type:
            cli += ' type ' + pn_type
        if dest_host:
            cli += ' dest-host ' + dest_host
        if community:
            cli += ' community ' + community
        if dest_port:
            cli += ' dest-port ' + dest_port

    if command == 'snmp-trap-sink-delete':
        if community:
            cli += ' community ' + community
        if dest_host:
            cli += ' dest-host ' + dest_host
        if dest_port:
            cli += ' dest-port ' + dest_port

    run_cli(module, cli)


if __name__ == '__main__':
    main()
