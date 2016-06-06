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
module: eos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary command on EOS device
description:
  - Sends an aribtrary set of commands to an EOS node and returns the results
    read from the device.  The M(eos_command) module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: eos
options:
  commands:
    description:
      - The commands to send to the remote EOS device over the
        configured provider.  The resulting output from the command
        is returned.  If the I(waitfor) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries has been exceeded.
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
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the waitfor
        conditionals
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
- eos_command:
    commands:
        - show interface {{ item }}
  with_items: interfaces

- eos_command:
    commands:
      - show version
    waitfor:
      - "result[0] contains 4.15.0F"

- eos_command:
  commands:
    - show version | json
    - show interfaces | json
    - show version
  waitfor:
    - "result[2] contains '4.15.0F'"
    - "result[1].interfaces.Management1.interfaceAddress[0].primaryIp.maskLen eq 24"
    - "result[0].modelName == 'vEOS'"
"""

RETURN = """
stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: the value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
  description: the conditionals that failed
  retured: failed
  type: list
  sample: ['...', '...']
"""
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcmd import CommandRunner, FailedConditionsError
from ansible.module_utils.network import NetworkError
from ansible.module_utils.eos import get_module

def to_lines(stdout):
    for item in stdout:
        if isinstance(item, basestring):
            item = str(item).split('\n')
        yield item

def main():
    spec = dict(
        commands=dict(type='list', required=True),
        wait_for=dict(type='list', aliases=['waitfor']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)

    commands = module.params['commands']
    conditionals = module.params['wait_for'] or list()

    warnings = list()

    runner = CommandRunner(module)

    for cmd in commands:
        if module.check_mode and not cmd.startswith('show'):
            warnings.append('only show commands are supported when using '
                            'check mode, not executing `%s`' % cmd)
        else:
            runner.add_command(cmd)

    for item in conditionals:
        runner.add_conditional(item)

    runner.retries = module.params['retries']
    runner.interval = module.params['interval']

    try:
        runner.run()
    except FailedConditionsError:
        exc = get_exception()
        module.fail_json(msg=str(exc), failed_conditions=exc.failed_conditions)
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

    result = dict(changed=False)

    result['stdout'] = list()
    for cmd in commands:
        try:
            output = runner.get_command(cmd)
            if cmd.endswith('json'):
                output = module.from_json(output)
        except ValueError:
            output = 'command not executed due to check_mode, see warnings'
        result['stdout'].append(output)


    result['warnings'] = warnings
    result['connected'] = module.connected
    result['stdout_lines'] = list(to_lines(result['stdout']))

    module.exit_json(**result)


if __name__ == '__main__':
    main()

