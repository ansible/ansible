#!/usr/bin/python
#
# (c) 2018 Extreme Networks Inc.
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
from __future__ import (absolute_import, division, print_function)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: slxos_command
version_added: "2.6"
author: "Lindsay Hill (@LindsayHill)"
short_description: Run commands on remote devices running Extreme Networks SLX-OS
description:
  - Sends arbitrary commands to an SLX node and returns the results
    read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
  - This module does not support running commands in configuration mode.
    Please use M(slxos_config) to configure SLX-OS devices.
notes:
  - Tested against SLX-OS 17s.1.02
  - If a command sent to the device requires answering a prompt, it is possible
    to pass a dict containing I(command), I(answer) and I(prompt). See examples.
options:
  commands:
    description:
      - List of commands to send to the remote SLX-OS device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries has expired.
    required: true
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    default: null
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    required: false
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    required: false
    default: 1
"""

EXAMPLES = """
tasks:
  - name: run show version on remote devices
    slxos_command:
      commands: show version

  - name: run show version and check to see if output contains SLX
    slxos_command:
      commands: show version
      wait_for: result[0] contains SLX

  - name: run multiple commands on remote nodes
    slxos_command:
      commands:
        - show version
        - show interfaces

  - name: run multiple commands and evaluate the output
    slxos_command:
      commands:
        - show version
        - show interface status
      wait_for:
        - result[0] contains SLX
        - result[1] contains Eth
  - name: run command that requires answering a prompt
    slxos_command:
      commands:
        - command: 'clear sessions'
          prompt: 'This operation will logout all the user sessions. Do you want to continue (yes/no)?:'
          answer: y
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import re
import time

from ansible.module_utils.network.slxos.slxos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


__metaclass__ = type


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def parse_commands(module, warnings):
    command = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict()
    ), module)
    commands = command(module.params['commands'])
    for item in list(commands):
        configure_type = re.match(r'conf(?:\w*)(?:\s+(\w+))?', item['command'])
        if module.check_mode:
            if configure_type and configure_type.group(1) not in ('confirm', 'replace', 'revert', 'network'):
                module.fail_json(
                    msg='slxos_command does not support running config mode '
                        'commands.  Please use slxos_config instead'
                )
            if not item['command'].startswith('show'):
                warnings.append(
                    'only show commands are supported when using check mode, not '
                    'executing `%s`' % item['command']
                )
                commands.remove(item)
    return commands


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    commands = parse_commands(module, warnings)
    result['warnings'] = warnings

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        responses = run_commands(module, commands)

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'changed': False,
        'stdout': responses,
        'stdout_lines': list(to_lines(responses))
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
