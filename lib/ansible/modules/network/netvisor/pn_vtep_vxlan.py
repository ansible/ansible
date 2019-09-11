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
module: pn_vtep_vxlan
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to add/remove vtep-vxlan
description:
  - This module can be used to add a VXLAN to a vtep and remove a VXLAN from a vtep.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - vtep-vxlan configuration command.
    required: false
    choices: ['present', 'absent']
    type: str
    default: 'present'
  pn_vtep_name:
    description:
      - vtep name.
    required: true
    type: str
  pn_vxlan:
    description:
      - VXLAN identifier.
    required: true
    type: str
"""

EXAMPLES = """

"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vtep-vxlan command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vtep-vxlan command.
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
    This method checks for idempotency using the vtep-show command.
    If a name exists, return True if name exists else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_vtep_name']

    cli += ' vtep-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vtep-vxlan-add',
        absent='vtep-vxlan-remove',
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_vtep_name=dict(required=True, type='str'),
        pn_vxlan=dict(required=True, type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    name = module.params['pn_vtep_name']
    vxlan = module.params['pn_vxlan']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)

    if NAME_EXISTS is False:
        module.exit_json(
            skipped=True,
            msg='vtep with name %s does not exist to add/remove vxlan' % name
        )

    cli += ' %s ' % command
    cli += ' name %s vxlan %s' % (name, vxlan)

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
