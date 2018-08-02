#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: cli_command
version_added: "2.7"
author: "Nathaniel Case (@qalthos)"
short_description: Run arbitrary commands on cli-based network devices
description:
  - Sends an arbitrary set of commands to a network device and returns the
    results read from the device.  This module includes an argument that
    will cause the module to wait for a specific condition before returning
    or timing out if the condition is not met.
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
        by the configured retries, the task fails.
        Note - With I(wait_for) the value in C(result['stdout']) can be accessed
        using C(result), that is to access C(result['stdout'][0]) use C(result[0]) See examples.
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
    default: all
    choices: ['any', 'all']
    version_added: "2.2"
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command.  If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    default: 1
"""

EXAMPLES = """
- name: run show version on remote devices
  cli_command:
    commands: show version

- name: run show version and check to see if output contains Arista
  cli_command:
    commands: show version
    wait_for: result[0] contains Arista

- name: run multiple commands on remote nodes
  cli_command:
    commands:
      - show version
      - show interfaces

- name: run multiple commands and evaluate the output
  cli_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Arista
      - result[1] contains Loopback0

- name: run commands and specify the output format
  cli_command:
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

from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import ComplexList

VALID_KEYS = ['command', 'output', 'prompt', 'response']


def to_lines(output):
    lines = []
    for item in output:
        if isinstance(item, string_types):
            item = to_text(item).split('\n')
        lines.append(item)
    return lines


def parse_commands(module, warnings):
    transform = ComplexList(dict(
        command=dict(key=True),
        output=dict(),
        prompt=dict(),
        answer=dict()
    ), module)

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
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    wait_for = module.params['wait_for'] or list()
    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as exc:
        module.fail_json(msg=to_text(exc))

    commands = parse_commands(module, warnings)
    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    connection = Connection(module._socket_path)
    for attempt in range(retries):
        responses = []
        try:
            for command in commands:
                responses.append(connection.get(**command))
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
