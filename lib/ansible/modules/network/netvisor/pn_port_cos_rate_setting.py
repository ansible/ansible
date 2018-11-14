#!/usr/bin/python
""" PN CLI port-cos-rate-setting-modify """

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
module: pn_port_cos_rate_setting
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to modify port-cos-rate-setting.
description:
  - C(modify): update the port cos rate limit
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use ''pdate' to modify
        the port-cos-rate-setting.
    required: True
  pn_cos1_rate:
    description:
      - cos1 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos5_rate:
    description:
      - cos5 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos2_rate:
    description:
      - cos2 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos0_rate:
    description:
      - cos0 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos6_rate:
    description:
      - cos6 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos3_rate:
    description:
      - cos3 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos4_rate:
    description:
      - cos4 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_cos7_rate:
    description:
      - cos7 rate limit (pps)
    required: false
    choices: ['unlimited', '0..10000000']
  pn_port:
    description:
      - port
    required: false
    choices: ['control-port', 'data-port', 'span-ports']
"""

EXAMPLES = """
- name: port cos rate modify
  pn_port_cos_rate_setting:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "control-port"
    pn_cos1_rate: "1000"
    pn_cos5_rate: "1000"
    pn_cos2_rate: "1000"
    pn_cos0_rate: "1000"

- name: port cos rate modify
  pn_port_cos_rate_setting:
    pn_cliswitch: "sw01"
    state: "update"
    pn_port: "data-port"
    pn_cos1_rate: "2000"
    pn_cos5_rate: "2000"
    pn_cos2_rate: "2000"
    pn_cos0_rate: "2000"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the port-cos-rate-setting command.
  returned: always
  type: list
stderr:
  description: set of error responses from the port-cos-rate-setting command.
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


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        update='port-cos-rate-setting-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_cos1_rate=dict(required=False, type='str'),
            pn_cos5_rate=dict(required=False, type='str'),
            pn_cos2_rate=dict(required=False, type='str'),
            pn_cos0_rate=dict(required=False, type='str'),
            pn_cos6_rate=dict(required=False, type='str'),
            pn_cos3_rate=dict(required=False, type='str'),
            pn_cos4_rate=dict(required=False, type='str'),
            pn_cos7_rate=dict(required=False, type='str'),
            pn_port=dict(required=False, type='str',
                         choices=['control-port', 'data-port', 'span-ports']),
        ),
        required_if=(
            ['state', 'update', ['pn_port']],
        ),
        required_one_of=[['pn_cos0_rate',
                          'pn_cos1_rate',
                          'pn_cos2_rate',
                          'pn_cos3_rate',
                          'pn_cos4_rate',
                          'pn_cos5_rate',
                          'pn_cos6_rate',
                          'pn_cos7_rate']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    cos1_rate = module.params['pn_cos1_rate']
    cos5_rate = module.params['pn_cos5_rate']
    cos2_rate = module.params['pn_cos2_rate']
    cos0_rate = module.params['pn_cos0_rate']
    cos6_rate = module.params['pn_cos6_rate']
    cos3_rate = module.params['pn_cos3_rate']
    cos4_rate = module.params['pn_cos4_rate']
    cos7_rate = module.params['pn_cos7_rate']
    port = module.params['pn_port']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'port-cos-rate-setting-modify':
        cli += ' %s ' % command
        if cos1_rate:
            cli += ' cos1-rate ' + cos1_rate
        if cos5_rate:
            cli += ' cos5-rate ' + cos5_rate
        if cos2_rate:
            cli += ' cos2-rate ' + cos2_rate
        if cos0_rate:
            cli += ' cos0-rate ' + cos0_rate
        if cos6_rate:
            cli += ' cos6-rate ' + cos6_rate
        if cos3_rate:
            cli += ' cos3-rate ' + cos3_rate
        if cos4_rate:
            cli += ' cos4-rate ' + cos4_rate
        if cos7_rate:
            cli += ' cos7-rate ' + cos7_rate
        if port:
            cli += ' port ' + port

    run_cli(module, cli)


if __name__ == '__main__':
    main()
