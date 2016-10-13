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
module: junos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Execute arbitrary commands on a remote device running Junos
description:
  - Network devices running the Junos operating system provide a command
    driven interface both over CLI and RPC.  This module provides an
    interface to execute commands using these functions and return the
    results to the Ansible playbook.  In addition, this
    module can specify a set of conditionals to be evaluated against the
    returned output, only returning control to the playbook once the
    entire set of conditionals has been met.
extends_documentation_fragment: junos
options:
  commands:
    description:
      - The C(commands) to send to the remote device over the Netconf
        transport.  The resulting output from the command
        is returned.  If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of I(retries) has been exceeded.
    required: false
    default: null
  rpcs:
    description:
      - The C(rpcs) argument accepts a list of RPCs to be executed
        over a netconf session and the results from the RPC execution
        is return to the playbook via the modules results dictionary.
    required: false
    default: null
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
      - Specifies the number of retries a command should by tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(waitfor)
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
  format:
    description:
      - Configures the encoding scheme to use when serializing output
        from the device.  This handles how to properly understand the
        output and apply the conditionals path to the result set.
    required: false
    default: 'xml'
    choices: ['xml', 'text']
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
vars:
  netconf:
    host: "{{ inventory_hostname }}"
    username: ansible
    password: Ansible

- name: run a set of commands
  junos_command:
    commands: ['show version', 'show ip route']
    provider: "{{ netconf }}"

- name: run a command with a conditional applied to the second command
  junos_command:
    commands:
      - show version
      - show interfaces fxp0
    waitfor:
      - "result[1].interface-information.physical-interface.name eq fxp0"
    provider: "{{ netconf }}"

- name: collect interface information using rpc
  junos_command:
    rpcs:
      - "get_interface_information interface=em0 media=True"
      - "get_interface_information interface=fxp0 media=True"
    provider: "{{ netconf }}"
"""

RETURN = """
stdout:
  description: The output from the commands read from the device
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The output read from the device split into lines
  returned: always
  type: list
  sample: [['...', '...'], ['...', '...']]

failed_conditionals:
  description: the conditionals that failed
  returned: failed
  type: list
  sample: ['...', '...']
"""

import ansible.module_utils.junos
from ansible.module_utils.basic import get_exception
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.netcli import CommandRunner
from ansible.module_utils.netcli import AddCommandError, FailedConditionsError
from ansible.module_utils.netcli import FailedConditionalError, AddConditionError
from ansible.module_utils.junos import xml_to_json
from ansible.module_utils.six import string_types

VALID_KEYS = {
    'cli': frozenset(['command', 'output', 'prompt', 'response']),
    'rpc': frozenset(['command', 'output'])
}


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item

def parse(module, command_type):
    if command_type == 'cli':
        items = module.params['commands']
    elif command_type == 'rpc':
        items = module.params['rpcs']

    parsed = list()
    for item in (items or list()):
        if isinstance(item, string_types):
            item = dict(command=item, output=None)
        elif 'command' not in item:
            module.fail_json(msg='command keyword argument is required')
        elif item.get('output') not in [None, 'text', 'xml']:
            module.fail_json(msg='invalid output specified for command'
                                 'Supported values are `text` or `xml`')
        elif not set(item.keys()).issubset(VALID_KEYS[command_type]):
            module.fail_json(msg='unknown command keyword specified.  Valid '
                                 'values are %s' % ', '.join(VALID_KEYS[command_type]))

        if not item['output']:
            item['output'] = module.params['display']

        item['command_type'] = command_type

        # show configuration [options] will return as text
        if item['command'].startswith('show configuration'):
            item['output'] = 'text'

        parsed.append(item)

    return parsed


def main():
    """main entry point for Ansible module
    """

    spec = dict(
        commands=dict(type='list'),
        rpcs=dict(type='list'),

        display=dict(default='xml', choices=['text', 'xml'],
                     aliases=['format', 'output']),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),

        transport=dict(default='netconf', choices=['netconf'])
    )

    mutually_exclusive = [('commands', 'rpcs')]

    module = NetworkModule(argument_spec=spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    commands = list()
    for key in VALID_KEYS.keys():
        commands.extend(list(parse(module, key)))

    conditionals = module.params['wait_for'] or list()

    warnings = list()

    runner = CommandRunner(module)

    for cmd in commands:
        if module.check_mode and not cmd['command'].startswith('show'):
            warnings.append('only show commands are supported when using '
                            'check mode, not executing `%s`' % cmd['command'])
        else:
            if cmd['command'].startswith('co'):
                module.fail_json(msg='junos_command does not support running '
                                     'config mode commands.  Please use '
                                     'junos_config instead')
            try:
                runner.add_command(**cmd)
            except AddCommandError:
                exc = get_exception()
                warnings.append('duplicate command detected: %s' % cmd)

    try:
        for item in conditionals:
            runner.add_conditional(item)
    except (ValueError, AddConditionError):
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
        module.fail_json(msg=str(exc))

    result = dict(changed=False, stdout=list())

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
