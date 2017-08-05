#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ops_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on OpenSwitch devices.
description:
  - Sends arbitrary commands to an OpenSwitch node and returns the results
    read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: openswitch
options:
  commands:
    description:
      - List of commands to send to the remote ops device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retires as expired.
    required: true
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
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
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between I(retries)
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
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
    username: netop
    password: netop
    transport: cli

---
- ops_command:
    commands:
      - show version
    provider: "{{ cli }}"

- ops_command:
    commands:
      - show version
    wait_for:
      - "result[0] contains OpenSwitch"
    provider: "{{ cli }}"

- ops_command:
    commands:
      - show version
      - show interfaces
    provider: "{{ cli }}"
"""

RETURN = """
stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
  description: the conditionals that failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import traceback

import ansible.module_utils.openswitch
from ansible.module_utils.netcli import CommandRunner
from ansible.module_utils.netcli import AddCommandError, FailedConditionsError
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native


VALID_KEYS = ['command', 'prompt', 'response']

def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item

def parse_commands(module):
    for cmd in module.params['commands']:
        if isinstance(cmd, string_types):
            cmd = dict(command=cmd, output=None)
        elif 'command' not in cmd:
            module.fail_json(msg='command keyword argument is required')
        elif not set(cmd.keys()).issubset(VALID_KEYS):
            module.fail_json(msg='unknown keyword specified')
        yield cmd

def main():
    spec = dict(
        # { command: <str>, prompt: <str>, response: <str> }
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = NetworkModule(argument_spec=spec,
                           connect_on_load=False,
                           supports_check_mode=True)

    commands = list(parse_commands(module))
    conditionals = module.params['wait_for'] or list()

    warnings = list()

    runner = CommandRunner(module)

    for cmd in commands:
        if module.check_mode and not cmd['command'].startswith('show'):
            warnings.append('only show commands are supported when using '
                            'check mode, not executing `%s`' % cmd['command'])
        else:
            if cmd['command'].startswith('conf'):
                module.fail_json(msg='ops_command does not support running '
                                     'config mode commands.  Please use '
                                     'ops_config instead')
            try:
                runner.add_command(**cmd)
            except AddCommandError:
                warnings.append('duplicate command detected: %s' % cmd)

    for item in conditionals:
        runner.add_conditional(item)

    runner.retries = module.params['retries']
    runner.interval = module.params['interval']
    runner.match = module.params['match']

    try:
        runner.run()
    except FailedConditionsError as e:
        module.fail_json(msg=to_native(e), failed_conditions=e.failed_conditions,
                         exception=traceback.format_exc())
    except NetworkError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    result = dict(changed=False, stdout=list())

    for cmd in commands:
        try:
            output = runner.get_command(cmd['command'])
        except ValueError:
            output = 'command not executed due to check_mode, see warnings'
        result['stdout'].append(output)

    result['warnings'] = warnings
    result['stdout_lines'] = list(to_lines(result['stdout']))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
