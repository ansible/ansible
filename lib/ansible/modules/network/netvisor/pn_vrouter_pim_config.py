#!/usr/bin/python
""" PN CLI vrouter-pim-config-modify """

# Copyright 2018 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_vrouter_pim_config
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to modify vrouter-pim-config.
description:
  - C(modify): modify pim parameters
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform.
        Use 'update' to modify the vrouter-pim-config.
    required: True
  pn_query_interval:
    description:
      - igmp query interval in seconds
    required: false
    type: str
  pn_querier_timeout:
    description:
      - igmp querier timeout in seconds
    required: false
    type: str
  pn_hello_interval:
    description:
      - hello interval in seconds
    required: false
    type: str
  pn_vrouter_name:
    description:
      - name of service config
    required: false
    type: str
"""

EXAMPLES = """
- name: pim config modify
  pn_vrouter_pim_config:
    pn_cliswitch: 'sw01'
    pn_query_interval: '10'
    pn_querier_timeout: '30'
    state: 'update'
    pn_vrouter_name: 'ansible-spine1-vrouter'
"""

RETURN = """
command:
  description: the CLI command run on the target node.
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

import shlex
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


def check_cli(module, cli):
    """
    This method checks for pim ssm config using the vrouter-show command.
    If a user already exists on the given switch, return PIM_SSM_CONFIG as
    True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: PIM_SSM_CONFIG.
    """
    # Global flags
    global PIM_SSM_CONFIG
    name = module.params['pn_vrouter_name']

    show = cli + ' vrouter-show name '
    show += '%s format proto-multi no-show-headers' % name
    show = shlex.split(show)
    out = module.run_command(show)[1]

    PIM_SSM_CONFIG = True if 'none' not in out else False


def main():
    """ This section is for arguments parsing """

    global state_map
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
        check_cli(module, cli)
        if PIM_SSM_CONFIG is False:
            module.exit_json(
                skipped=True,
                msg='vrouter proto-multi is not configured'
            )
        cli += ' %s vrouter-name %s ' % (command, vrouter_name)
        if querier_timeout:
            cli += ' querier-timeout ' + querier_timeout
        if hello_interval:
            cli += ' hello-interval ' + hello_interval
        if query_interval:
            cli += ' query-interval ' + query_interval

    run_cli(module, cli)


if __name__ == '__main__':
    main()
