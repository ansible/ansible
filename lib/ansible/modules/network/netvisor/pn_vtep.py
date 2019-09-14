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
module: pn_vtep
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.9"
short_description: CLI command to create/delete vtep
description:
  - This module can be used to create a vtep and delete a vtep.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - vtep configuration command.
    required: false
    choices: ['present', 'absent']
    type: str
    default: 'present'
  pn_name:
    description:
      - vtep name.
    required: false
    type: str
  pn_ip:
    description:
      - Primary IP address.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of the vrouter service.
    required: false
    type: str
  pn_virtual_ip:
    description:
      - Virtual/Secondary IP address.
    required: false
    type: str
  pn_location:
    description:
      - switch name.
    required: false
    type: str
  pn_switch_in_cluster:
    description:
      - Tells whether switch in cluster or not.
    required: false
    type: bool
    default: True
"""

EXAMPLES = """
- name: create vtep
  pn_vtep:
    pn_cliswitch: 'sw01'
    pn_name: 'foo'
    pn_vrouter_name: 'foo-vrouter'
    pn_ip: '22.22.22.2'
    pn_location: 'sw01'
    pn_virtual_ip: "22.22.22.1"

- name: delete vtep
  pn_vtep:
    pn_cliswitch: 'sw01'
    state: 'absent'
    pn_name: 'foo'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vtep command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vtep command.
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
    name = module.params['pn_name']

    cli += ' vtep-show format name no-show-headers'
    out = run_commands(module, cli)[1]

    if out:
        out = out.split()

    return True if name in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        present='vtep-create',
        absent='vtep-delete'
    )

    argument_spec = dict(
        pn_cliswitch=dict(required=False, type='str'),
        state=dict(required=False, type='str', choices=state_map.keys(), default='present'),
        pn_name=dict(required=False, type='str'),
        pn_ip=dict(required=False, type='str'),
        pn_vrouter_name=dict(required=False, type='str'),
        pn_virtual_ip=dict(required=False, type='str'),
        pn_location=dict(required=False, type='str'),
        pn_switch_in_cluster=dict(required=False, type='bool', default='True')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(
            ["state", "present", ["pn_name", "pn_ip", "pn_vrouter_name", "pn_location"]],
            ["state", "absent", ["pn_name"]],
        ),
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    name = module.params['pn_name']
    ip = module.params['pn_ip']
    vrouter_name = module.params['pn_vrouter_name']
    virtual_ip = module.params['pn_virtual_ip']
    location = module.params['pn_location']
    switch_in_cluster = module.params['pn_switch_in_cluster']

    if switch_in_cluster and not virtual_ip and state == 'present':
        module.exit_json(
            failed=True,
            msg='virtual ip is required when switch is in cluster'
        )

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    NAME_EXISTS = check_cli(module, cli)

    cli += ' %s name %s ' % (command, name)

    if command == 'vtep-delete':
        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vtep with name %s does not exist' % name
            )

    if command == 'vtep-create':
        if NAME_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='vtpe with name %s already exists' % name
            )

        cli += 'vrouter-name %s ' % vrouter_name
        cli += 'ip %s ' % ip
        cli += 'location %s ' % location

        if virtual_ip:
            cli += 'virtual-ip %s ' % virtual_ip

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
