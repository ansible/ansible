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
short_description: Run a cli command on cli-based network devices
description:
  - Sends a command to a network device and returns the result read from the device.
extends_documentation_fragment: network_agnostic
options:
  command:
    description:
      - The command to send to the remote network device.  The resulting output
        from the command is returned, unless I(sendonly) is set.
    required: true
  prompt:
    description:
      - A single regex pattern or a sequence of patterns to evaluate the expected
        prompt from I(command).
    required: false
    type: list
  answer:
    description:
      - The answer to reply with if I(prompt) is matched. The value can be a single answer
        or a list of answer for multiple prompts. In case the command execution results in
        multiple prompts the sequence of the prompt and excepted answer should be in same order.
    required: false
    type: list
  sendonly:
    description:
      - The boolean value, that when set to true will send I(command) to the
        device but not wait for a result.
    type: bool
    default: false
    required: false
  check_all:
    description:
      - By default if any one of the prompts mentioned in C(prompt) option is matched it won't check
        for other prompts. This boolean flag, that when set to I(True) will check for all the prompts
        mentioned in C(prompt) option in the given order. If the option is set to I(True) all the prompts
        should be received from remote host if not it will result in timeout.
    type: bool
    default: false
"""

EXAMPLES = """
- name: run show version on remote devices
  cli_command:
    command: show version

- name: run command with json formatted output
  cli_command:
    command: show version | json

- name: run command expecting user confirmation
  cli_command:
    command: commit replace
    prompt: This commit will replace or remove the entire running configuration
    answer: yes

- name: run config mode command and handle prompt/answer
  cli_command:
    command: "{{ item }}"
    prompt:
      - "Exit with uncommitted changes"
    answer: 'y'
  loop:
    - configure
    - set system syslog file test any any
    - exit

- name: multiple prompt, multiple answer (mandatory check for all prompts)
  cli_command:
    command: "copy sftp sftp://user@host//user/test.img"
    check_all: True
    prompt:
      - "Confirm download operation"
      - "Password"
      - "Do you want to change that to the standby image"
    answer:
      - 'y'
      - <password>
      - 'y'
"""

RETURN = """
stdout:
  description: The response from the command
  returned: when sendonly is false
  type: str
  sample: 'Version:      VyOS 1.1.7[...]'

json:
  description: A dictionary representing a JSON-formatted response
  returned: when the device response is valid JSON
  type: dict
  sample: |
    {
      "architecture": "i386",
      "bootupTimestamp": 1532649700.56,
      "modelName": "vEOS",
      "version": "4.15.9M"
      [...]
    }
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        command=dict(type='str', required=True),
        prompt=dict(type='list', required=False),
        answer=dict(type='list', required=False),
        sendonly=dict(type='bool', default=False, required=False),
        check_all=dict(type='bool', default=False, required=False),
    )
    required_together = [['prompt', 'answer']]
    module = AnsibleModule(argument_spec=argument_spec, required_together=required_together,
                           supports_check_mode=True)

    if module.check_mode and not module.params['command'].startswith('show'):
        module.fail_json(
            msg='Only show commands are supported when using check_mode, not '
            'executing %s' % module.params['command']
        )

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    connection = Connection(module._socket_path)
    response = ''
    try:
        response = connection.get(**module.params)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    if not module.params['sendonly']:
        try:
            result['json'] = module.from_json(response)
        except ValueError:
            pass

        result.update({
            'stdout': response,
        })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
