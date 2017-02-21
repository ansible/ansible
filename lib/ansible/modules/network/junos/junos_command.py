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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'core',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: junos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on an Juniper junos device
description:
  - Sends an arbitrary set of commands to an junos node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
options:
  commands:
    description:
      - The commands to send to the remote junos device over the
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
- name: run show version on remote devices
  junos_command:
    commands: show version

- name: run show version and check to see if output contains Juniper
  junos_command:
    commands: show version
    wait_for: result[0] contains Juniper

- name: run multiple commands on remote nodes
  junos_command:
    commands:
      - show version
      - show interfaces

- name: run multiple commands and evaluate the output
  junos_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Juniper
      - result[1] contains Loopback0

- name: run commands and specify the output format
  junos_command:
    commands:
      - command: show version
        output: json
"""

RETURN = """
failed_conditions:
  description: the conditionals that failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import time

from functools import partial

from ansible.module_utils.junos import run_commands
from ansible.module_utils.junos import junos_argument_spec
from ansible.module_utils.junos import check_args as junos_check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.network_common import ComplexList

def check_args(module, warnings):
    junos_check_args(module, warnings)

    if module.params['rpcs']:
        module.fail_json(msg='argument rpcs has been deprecated, please use '
                             'junos_rpc instead')

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
        output=dict(default=module.params['display'], choices=['text', 'json']),
        prompt=dict(),
        response=dict()
    )

    transform = ComplexList(spec, module)
    commands = transform(module.params['commands'])

    for index, item in enumerate(commands):
        if module.check_mode and not item['command'].startswith('show'):
            warnings.append(
                'Only show commands are supported when using check_mode, not '
                'executing %s' % item['command']
            )

        if item['output'] == 'json' and 'display json' not in item['command']:
            item['command'] += '| display json'
        elif item['output'] == 'text' and 'display json' in item['command']:
            item['command'] = item['command'].replace('| display json', '')

        commands[index] = item

    return commands

def main():
    """entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),
        display=dict(choices=['text', 'json'], default='text'),

        # deprecated (Ansible 2.3) - use junos_rpc
        rpcs=dict(type='list'),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)


    warnings = list()
    check_args(module, warnings)

    commands = parse_commands(module, warnings)

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
        msg = 'One or more conditional statements have not be satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result = {
        'changed': False,
        'warnings': warnings,
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    }


    module.exit_json(**result)


if __name__ == '__main__':
    main()
