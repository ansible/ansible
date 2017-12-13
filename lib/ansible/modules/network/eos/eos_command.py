#!/usr/bin/python
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
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: eos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on an Arista EOS device
description:
  - Sends an arbitrary set of commands to an EOS node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: eos
notes:
  - Tested against EOS 4.15
options:
  commands:
    description:
      - The commands to send to the remote EOS device over the
        configured provider.  The resulting output from the command
        is returned.  If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of I(retries) has been exceeded.
    required: true
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward.   If the conditional is not true
        by the configured retries, the task fails.  See examples.
    required: false
    default: null
    aliases: ['waitfor']
    version_added: "2.2"
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the I(wait_for) must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    required: false
    default: all
    choices: ['any', 'all']
    version_added: "2.2"
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command.  If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    required: false
    default: 1
"""

EXAMPLES = """
- name: run show version on remote devices
  eos_command:
    commands: show version

- name: run show version and check to see if output contains Arista
  eos_command:
    commands: show version
    wait_for: result[0] contains Arista

- name: run multiple commands on remote nodes
  eos_command:
    commands:
      - show version
      - show interfaces

- name: run multiple commands and evaluate the output
  eos_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Arista
      - result[1] contains Loopback0

- name: run commands and specify the output format
  eos_command:
    commands:
      - command: show version
        output: json
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
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import string_types
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.eos.eos import run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args

VALID_KEYS = ['command', 'output', 'prompt', 'response']


def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        lines.append(item)
    return lines


def parse_commands(module, warnings):
    spec = dict(
        command=dict(key=True),
        output=dict(),
        prompt=dict(),
        answer=dict()
    )

    transform = ComplexList(spec, module)
    commands = transform(module.params['commands'])

    if module.check_mode:
        for item in list(commands):
            if not item['command'].startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check_mode, not '
                    'executing %s' % item['command']
                )
                commands.remove(item)

    return commands


def to_cli(obj):
    cmd = obj['command']
    if obj.get('output') == 'json':
        cmd += ' | json'
    return cmd


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    commands = parse_commands(module, warnings)
    if warnings:
        result['warnings'] = warnings

    wait_for = module.params['wait_for'] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

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
        msg = 'One or more conditional statements have not be satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'changed': False,
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
