#!/usr/bin/python
""" PN-CLI vrouter-ospf-add/remove """

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
module: pn_ospfarea
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to add/remove ospf area to/from a vrouter.
description:
  - Execute vrouter-ospf-add, vrouter-ospf-remove command.
  - This command adds/removes Open Shortest Path First(OSPF) area to/from
    a virtual router(vRouter) service.
options:
  pn_cliusername:
    description:
      - Login username.
    required: true
  pn_clipassword:
    description:
      - Login password.
    required: true
  pn_cliswitch:
    description:
      - Target switch(es) to run the CLI on.
    required: False
  state:
    description:
      - State the action to perform. Use 'present' to add ospf-area, 'absent'
        to remove ospf-area and 'update' to modify ospf-area.
    required: true
    choices: ['present', 'absent', 'update']
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter.
    required: true
  pn_ospf_area:
    description:
      - Specify the OSPF area number.
    required: true
  pn_stub_type:
    description:
      - Specify the OSPF stub type.
    choices: ['none', 'stub', 'stub-no-summary', 'nssa', 'nssa-no-summary']
  pn_prefix_listin:
    description:
      - OSPF prefix list for filtering incoming packets.
  pn_prefix_listout:
    description:
      - OSPF prefix list for filtering outgoing packets.
  pn_quiet:
    description:
      - Enable/disable system information.
    required: false
    default: true
"""

EXAMPLES = """
- name: "Add OSPF area to vrouter"
  pn_ospfarea:
    state: present
    pn_cliusername: admin
    pn_clipassword: admin
    pn_ospf_area: 1.0.0.0
    pn_stub_type: stub

- name: "Remove OSPF from vrouter"
  pn_ospf:
    state: absent
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vrouter_name: name-string
    pn_ospf_area: 1.0.0.0
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the ospf command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the ospf command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex


def get_command_from_state(state):
    """
    This method gets appropriate command name for the state specified. It
    returns the command name for the specified state.
    :param state: The state for which the respective command name is required.
    """
    command = None
    if state == 'present':
        command = 'vrouter-ospf-area-add'
    if state == 'absent':
        command = 'vrouter-ospf-area-remove'
    if state == 'update':
        command = 'vrouter-ospf-area-modify'
    return command


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent', 'update']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_ospf_area=dict(required=True, type='str'),
            pn_stub_type=dict(type='str', choices=['none', 'stub', 'nssa',
                                                   'stub-no-summary',
                                                   'nssa-no-summary']),
            pn_prefix_listin=dict(type='str'),
            pn_prefix_listout=dict(type='str'),
            pn_quiet=dict(type='bool', default='True')
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    vrouter_name = module.params['pn_vrouter_name']
    ospf_area = module.params['pn_ospf_area']
    stub_type = module.params['pn_stub_type']
    prefix_listin = module.params['pn_prefix_listin']
    prefix_listout = module.params['pn_prefix_listout']
    quiet = module.params['pn_quiet']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = '/usr/bin/cli'

    if quiet is True:
        cli += ' --quiet '

    cli += ' --user %s:%s ' % (cliusername, clipassword)

    if cliswitch:
        if cliswitch == 'local':
            cli += ' switch-local '
        else:
            cli += ' switch ' + cliswitch

    cli += ' %s vrouter-name %s area %s ' % (command, vrouter_name, ospf_area)

    if stub_type:
        cli += ' stub-type ' + stub_type

    if prefix_listin:
        cli += ' prefix-list-in ' + prefix_listin

    if prefix_listout:
        cli += ' prefix-list-out ' + prefix_listout

    # Run the CLI command
    ospfcommand = shlex.split(cli)

    # 'out' contains the output
    # 'err' contains the error messages
    result, out, err = module.run_command(ospfcommand)

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
