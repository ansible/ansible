#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_command
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Run arbitrary commands on remote Ruckus ICX 7000 series switches
description:
  - Sends arbitrary commands to an ICX node and returns the results
    read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
notes:
  - Tested against ICX 10.1
options:
  commands:
    description:
      - List of commands to send to the remote ICX device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries has expired. If a command sent to the
        device requires answering a prompt, checkall and newline if
        multiple prompts, it is possible to pass
        a dict containing I(command), I(answer), I(prompt), I(check_all)
        and I(newline).Common answers are 'y' or "\\r" (carriage return,
        must be double quotes). See examples.
    type: list
    required: true
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    type: list
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    type: str
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of times a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    type: int
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    type: int
    default: 1
"""

EXAMPLES = """
tasks:
  - name: run show version on remote devices
    icx_command:
      commands: show version

  - name: run show version and check to see if output contains ICX
    icx_command:
      commands: show version
      wait_for: result[0] contains ICX

  - name: run multiple commands on remote nodes
    icx_command:
      commands:
        - show version
        - show interfaces

  - name: run multiple commands and evaluate the output
    icx_command:
      commands:
        - show version
        - show interfaces
      wait_for:
        - result[0] contains ICX
        - result[1] contains GigabitEthernet1/1/1
  - name: run commands that require answering a prompt
    icx_command:
      commands:
        - command: 'service password-encryption sha1'
          prompt: 'Warning: Moving to higher password-encryption type,.*'
          answer: 'y'
  - name: run commands that require answering multiple prompt
    icx_command:
      commands:
        - command: 'username qqq password qqq'
          prompt:
            - 'User already exists. Do you want to modify:.*'
            - 'To modify or remove user, enter current password:'
          answer:
            - 'y'
            - 'qqq\\\r'
          check_all: True
          newline: False
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors
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
from ansible.module_utils.network.icx.icx import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList, to_lines
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def parse_commands(module, warnings):
    command = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict(),
        check_all=dict(type='bool', default='False'),
        newline=dict(type='bool', default='True')
    ), module)
    commands = command(module.params['commands'])
    for item in list(commands):
        if module.check_mode:
            if not item['command'].startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check mode, not executing configure terminal')
                commands.remove(item)
    return commands


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    run_commands(module, ['skip'])
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
