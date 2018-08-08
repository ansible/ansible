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
options:
  commands:
    description:
      - The commands to send to the remote EOS device over the
        configured provider.  The resulting output from the command
        is returned.
    required: true
"""

EXAMPLES = """
- name: run show version on remote devices
  cli_command:
    commands: show version

- name: run multiple commands on remote nodes
  cli_command:
    commands:
      - show version
      - show interfaces

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
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.utils import ComplexList

VALID_KEYS = ['command', 'output', 'prompt', 'response']


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

        match=dict(default='all', choices=['all', 'any']),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    commands = parse_commands(module, warnings)

    connection = Connection(module._socket_path)
    responses = []
    try:
        for command in commands:
            responses.append(connection.get(**command))
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    result.update({
        'stdout': responses,
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
