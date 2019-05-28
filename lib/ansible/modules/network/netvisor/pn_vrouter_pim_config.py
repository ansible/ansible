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
module: pn_vrouter_pim_config
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify vrouter-pim-config
description:
  - This module can be used to modify pim parameters.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the vrouter-pim-config.
    required: true
    type: str
    choices: ['update']
  pn_query_interval:
    description:
      - igmp query interval in seconds.
    required: false
    type: str
  pn_querier_timeout:
    description:
      - igmp querier timeout in seconds.
    required: false
    type: str
  pn_hello_interval:
    description:
      - hello interval in seconds.
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config.
    required: false
    type: str
"""

EXAMPLES = """
- name: pim config modify
  pn_vrouter_pim_config:
    pn_cliswitch: '192.168.1.1'
    pn_query_interval: '10'
    pn_querier_timeout: '30'
    state: 'update'
    pn_vrouter_name: 'ansible-spine1-vrouter'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the vrouter-pim-config command.
  returned: always
  type: list
stderr:
  description: set of error responses from the vrouter-pim-config command.
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
    This method checks for pim ssm config using the vrouter-show command.
    If a user already exists on the given switch, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    """
    name = module.params['pn_vrouter_name']

    show = cli
    cli += ' vrouter-show format name no-show-headers '
    out = run_commands(module, cli)[1]
    if out:
        out = out.split()
    if name in out:
        pass
    else:
        return False

    cli = show
    cli += ' vrouter-show name %s format proto-multi no-show-headers' % name
    out = run_commands(module, cli)[1]
    if out:
        out = out.split()

    return True if 'none' not in out else False


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='vrouter-pim-config-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_query_interval=dict(required=False, type='str'),
            pn_querier_timeout=dict(required=False, type='str'),
            pn_hello_interval=dict(required=False, type='str'),
            pn_vrouter_name=dict(required=True, type='str'),
        ),
        required_if=(
            ['state', 'update', ['pn_vrouter_name']],
        ),
        required_one_of=[['pn_query_interval',
                          'pn_querier_timeout',
                          'pn_hello_interval']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    query_interval = module.params['pn_query_interval']
    querier_timeout = module.params['pn_querier_timeout']
    hello_interval = module.params['pn_hello_interval']
    vrouter_name = module.params['pn_vrouter_name']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'vrouter-pim-config-modify':
        PIM_SSM_CONFIG = check_cli(module, cli)
        if PIM_SSM_CONFIG is False:
            module.exit_json(
                skipped=True,
                msg='vrouter proto-multi is not configured/vrouter is not created'
            )
        cli += ' %s vrouter-name %s ' % (command, vrouter_name)
        if querier_timeout:
            cli += ' querier-timeout ' + querier_timeout
        if hello_interval:
            cli += ' hello-interval ' + hello_interval
        if query_interval:
            cli += ' query-interval ' + query_interval

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
