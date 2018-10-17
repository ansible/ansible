#!/usr/bin/python

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: edgeos_command
version_added: "2.5"
author:
  - Chad Norgan (@BeardyMcBeards)
  - Sam Doran (@samdoran)
short_description: Run one or more commands on EdgeOS devices
description:
  - This command module allows running one or more commands on a remote
    device running EdgeOS, such as the Ubiquiti EdgeRouter.
  - This module does not support running commands in configuration mode.
  - Certain C(show) commands in EdgeOS produce many lines of output and
    use a custom pager that can cause this module to hang.  If the
    value of the environment variable C(ANSIBLE_EDGEOS_TERMINAL_LENGTH)
    is not set, the default number of 10000 is used.
  - "This is a network module and requires C(connection: network_cli)
    in order to work properly."
  - For more information please see the L(Network Guide,../network/getting_started/index.html).
options:
  commands:
    description:
      - The commands or ordered set of commands that should be run against the
        remote device. The output of the command is returned to the playbook.
        If the C(wait_for) argument is provided, the module is not returned
        until the condition is met or the number of retries is exceeded.
    required: True
  wait_for:
    description:
      - Causes the task to wait for a specific condition to be met before
        moving forward. If the condition is not met before the specified
        number of retries is exceeded, the task will fail.
    required: False
  match:
    description:
      - Used in conjunction with C(wait_for) to create match policy. If set to
        C(all), then all conditions in C(wait_for) must be met. If set to
        C(any), then only one condition must match.
    required: False
    default: 'all'
    choices: ['any', 'all']
  retries:
    description:
      - Number of times a command should be tried before it is considered failed.
        The command is run on the target device and evaluated against the
        C(wait_for) conditionals.
    required: False
    default: 10
  interval:
    description:
      - The number of seconds to wait between C(retries) of the command.
    required: False
    default: 1

notes:
  - Tested against EdgeOS 1.9.7
  - Running C(show system boot-messages all) will cause the module to hang since
    EdgeOS is using a custom pager setting to display the output of that command.
"""

EXAMPLES = """
tasks:
  - name: Reboot the device
    edgeos_command:
      commands: reboot now

  - name: Show the configuration for eth0 and eth1
    edgeos_command:
      commands: show interfaces ethernet {{ item }}
    loop:
      - eth0
      - eth1
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
"""

import time

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.edgeos.edgeos import run_commands
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = to_text(item).split('\n')
        yield item


def parse_commands(module, warnings):
    spec = dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict(),
    )

    transform = ComplexList(spec, module)
    commands = transform(module.params['commands'])

    if module.check_mode:
        for item in list(commands):
            if not item['command'].startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check_mode, '
                    'not executing %s' % item['command'])
                commands.remove(item)

    return commands


def main():
    spec = dict(
        commands=dict(type='list', required=True),
        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    warnings = list()
    result = {'changed': False}
    commands = parse_commands(module, warnings)
    wait_for = module.params['wait_for'] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as e:
        module.fail_json(msg=to_text(e))

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

    result = {
        'changed': False,
        'stdout': responses,
        'warnings': warnings,
        'stdout_lines': list(to_lines(responses))
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
