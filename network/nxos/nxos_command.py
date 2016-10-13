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

DOCUMENTATION = """
---
module: nxos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary command on Cisco NXOS devices
description:
  - Sends an arbitrary command to an NXOS node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: nxos
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
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: admin
    password: admin
    transport: cli

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
import ansible.module_utils.nxos

from ansible.module_utils.basic import get_exception
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.netcli import CommandRunner
from ansible.module_utils.netcli import FailedConditionsError
from ansible.module_utils.netcli import FailedConditionalError
from ansible.module_utils.netcli import AddCommandError, AddConditionError

VALID_KEYS = ['command', 'output', 'prompt', 'response']

def to_lines(stdout):
    for item in stdout:
        if isinstance(item, basestring):
            item = str(item).split('\n')
        yield item

def parse_commands(module):
    for cmd in module.params['commands']:
        if isinstance(cmd, basestring):
            cmd = dict(command=cmd, output=None)
        elif 'command' not in cmd:
            module.fail_json(msg='command keyword argument is required')
        elif cmd.get('output') not in [None, 'text', 'json']:
            module.fail_json(msg='invalid output specified for command')
        elif not set(cmd.keys()).issubset(VALID_KEYS):
            module.fail_json(msg='unknown keyword specified')
        yield cmd

def main():
    spec = dict(
        # { command: <str>, output: <str>, prompt: <str>, response: <str> }
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['any', 'all']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = NetworkModule(argument_spec=spec,
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
                module.fail_json(msg='nxos_command does not support running '
                                     'config mode commands.  Please use '
                                     'nxos_config instead')
            try:
                runner.add_command(**cmd)
            except AddCommandError:
                exc = get_exception()
                warnings.append('duplicate command detected: %s' % cmd)

    try:
        for item in conditionals:
            runner.add_conditional(item)
    except AddConditionError:
        exc = get_exception()
        module.fail_json(msg=str(exc), condition=exc.condition)

    runner.retries = module.params['retries']
    runner.interval = module.params['interval']
    runner.match = module.params['match']

    try:
        runner.run()
    except FailedConditionsError:
        exc = get_exception()
        module.fail_json(msg=str(exc), failed_conditions=exc.failed_conditions)
    except FailedConditionalError:
        exc = get_exception()
        module.fail_json(msg=str(exc), failed_conditional=exc.failed_conditional)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc), **exc.kwargs)

    result = dict(changed=False)

    result['stdout'] = list()
    for cmd in commands:
        try:
            output = runner.get_command(cmd['command'], cmd.get('output'))
        except ValueError:
            output = 'command not executed due to check_mode, see warnings'
        result['stdout'].append(output)

    result['warnings'] = warnings
    result['stdout_lines'] = list(to_lines(result['stdout']))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
