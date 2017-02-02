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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: nxos_command
extends_documentation_fragment: nxos
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary command on Cisco NXOS devices
description:
  - Sends an arbitrary command to an NXOS node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
options:
  commands:
    description:
      - The commands to send to the remote NXOS device over the
        configured provider.  The resulting output from the command
        is returned.  If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retires as expired.
      - The I(commands) argument also accepts an alternative form
        that allows for complex values that specify the command
        to run and the output format to return.   This can be done
        on a command by command basis.  The complex argument supports
        the keywords C(command) and C(output) where C(command) is the
        command to run and C(output) is one of 'text' or 'json'.
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
    version_added: "2.2"
  retries:
    description:
      - Specifies the number of retries a command should by tried
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

---
- name: run show version on remote devices
  nxos_command:
    commands: show version
    provider: "{{ cli }}"

- name: run show version and check to see if output contains Cisco
  nxos_command:
    commands: show version
    wait_for: result[0] contains Cisco
    provider: "{{ cli }}"

- name: run multiple commands on remote nodes
  nxos_command:
    commands:
      - show version
      - show interfaces
    provider: "{{ cli }}"

- name: run multiple commands and evaluate the output
  nxos_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Cisco
      - result[1] contains loopback0
    provider: "{{ cli }}"

- name: run commands and specify the output format
  nxos_command:
    commands:
      - command: show version
        output: json
    provider: "{{ cli }}"
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

from ansible.module_utils.nxos import run_commands
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.netcli import Conditional, FailedConditionalError
from ansible.module_utils.network_common import ComplexList
from ansible.module_utils.nxos import nxos_argument_spec, check_args

def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
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

    for index, item in enumerate(commands):
        if module.check_mode and not item['command'].startswith('show'):
            warnings.append(
                'Only show commands are supported when using check_mode, not '
                'executing %s' % item['command']
            )

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
        # { command: <str>, output: <str>, prompt: <str>, response: <str> }
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['any', 'all']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)


    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    commands = parse_commands(module, warnings)
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
            try:
                if item(responses):
                    if match == 'any':
                        conditionals = list()
                        break
                    conditionals.remove(item)
            except FailedConditionalError:
                exc = get_exception()
                module.fail_json(msg=str(exc))

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not be satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
