#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2017 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
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
# Module to execute ENOS Commands on Lenovo Switches.
# Lenovo Networking
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: enos_command
version_added: "2.5"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Run arbitrary commands on Lenovo ENOS devices
description:
  - Sends arbitrary commands to an ENOS node and returns the results
    read from the device. The C(enos_command) module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: enos
options:
  commands:
    description:
      - List of commands to send to the remote device over the
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
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    port: 22
    username: admin
    password: admin
    timeout: 30

---
- name: test contains operator
  enos_command:
    commands:
      - show version
      - show system memory
    wait_for:
      - "result[0] contains 'Lenovo'"
      - "result[1] contains 'MemFree'"
    provider: "{{ cli }}"
  register: result

- assert:
    that:
      - "result.changed == false"
      - "result.stdout is defined"

- name: get output for single command
  enos_command:
    commands: ['show version']
    provider: "{{ cli }}"
  register: result

- assert:
    that:
      - "result.changed == false"
      - "result.stdout is defined"

- name: get output for multiple commands
  enos_command:
    commands:
      - show version
      - show interface information
    provider: "{{ cli }}"
  register: result

- assert:
    that:
      - "result.changed == false"
      - "result.stdout is defined"
      - "result.stdout | length == 2"
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

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.enos.enos import run_commands, check_args
from ansible.module_utils.network.enos.enos import enos_argument_spec
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def main():
    spec = dict(
        # { command: <str>, prompt: <str>, response: <str> }
        commands=dict(type='list', required=True),

        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    spec.update(enos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    result = {'changed': False}

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

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

    result.update({
        'changed': False,
        'stdout': responses,
        'stdout_lines': list(to_lines(responses))
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
