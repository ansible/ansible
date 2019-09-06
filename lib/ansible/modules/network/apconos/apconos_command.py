#!/usr/bin/python
#
# Copyright (C) 2019 APCON.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to execute apconos Commands on Apcon Switches.
# Apcon Networking

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: apconos_command
version_added: "2.9"
author: "David Lee (@davidlee-ap)"
short_description: Run arbitrary commands on APCON devices
description:
  - Sends arbitrary commands to an apcon device and returns the results
    read from the device. The module includes an argument that will
    cause the module to wait for a specific condition before returning
    or timing out if the condition is not met.
notes:
  - Tested against apcon iis+ii
options:
  commands:
    description:
      - List of commands to send to the remote device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retires as expired.
    required: true
  provider:
    description:
      - Please use connetcion network_cli.
  auth_pass:
    description:
      - Specifies the password to use if required to enter privileged mode
        on the remote device.  If I(authorize) is false, then this argument
        does nothing. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
    type: str
  authorize:
    description:
      - Instructs the module to enter privileged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to execute all commands in non-privileged mode. If the value
        is not specified in the task, the value of environment variable
        C(ANSIBLE_NET_AUTHORIZE) will be used instead.
    type: bool
    default: no
  host:
    description:
      - Specifies the DNS host name or address for connecting to the remote
        device over the specified transport.  The value of host is used as
        the destination address for the transport.
    type: str
    required: true
  port:
    description:
      - Specifies the port to use when building the connection to the remote device.
    type: int
    default: 22
  username:
    description:
      - Configures the username to use to authenticate the connection to
        the remote device.  This value is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
    type: str
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.   This value is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
    type: str
  timeout:
    description:
      - Specifies the timeout in seconds for communicating with the network device
        for either connecting or sending commands.  If the timeout is
        exceeded before the operation is completed, the module will error.
    type: int
    default: 10
  ssh_keyfile:
    description:
      - Specifies the SSH key to use to authenticate the connection to
        the remote device.   This value is the path to the
        key used to authenticate the SSH session. If the value is not specified
        in the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
        will be used instead.
    type: path
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    default: 1
"""

EXAMPLES = """
- name: Basic Configuration
  apconos_command:
    commands:
    - show version
    - enable ssh
  register: result

- name: Get output from single command
  apconos_command:
    commands: ['show version']
  register: result
"""

RETURN = """
"""

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import transform_commands, to_lines
from ansible.module_utils.network.apconos.apconos import run_commands, check_args
from ansible.module_utils.network.apconos.apconos import apconos_argument_spec
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def parse_commands(module, warnings):

    commands = module.params['commands']

    if module.check_mode:
        for item in list(commands):
            if not item.startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check mode, not '
                    'executing %s' % item
                )
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

    spec.update(apconos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    commands = parse_commands(module, warnings)
    commands = module.params['commands']
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

    for item in responses:
        if len(item) == 0:
            if module.check_mode:
                result.update({
                    'changed': False,
                    'stdout': responses,
                    'stdout_lines': list(to_lines(responses))
                })
            else:
                result.update({
                    'changed': True,
                    'stdout': responses,
                    'stdout_lines': list(to_lines(responses))
                })
        elif 'ERROR' in item:
            result.update({
                'failed': True,
                'stdout': responses,
                'stdout_lines': list(to_lines(responses))
            })
        else:
            result.update({
                'stdout': item,
                'stdout_lines': list(to_lines(responses))
            })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
