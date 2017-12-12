#!/usr/bin/python

# Copyright: (c) 2017, Ansible Project
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
    device running the EdgeOS, such as the Ubiquiti EdgeRouter.
options:
  commands:
    description:
      - The commands or ordered set of commands that should be run against the
        remote device.
    required: true
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
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.edgeos.edgeos import run_commands
from ansible.module_utils.network.edgeos.edgeos import edgeos_argument_spec
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def parse_commands(module, warnings):
    command = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict(),
    ), module)
    commands = command(module.params['commands'])
    items = []

    for item in commands:
        if module.check_mode and not item['command'].startswith('show'):
            warnings.append('only \'show\' commands are supported when using '
                            'check mode, not executing \'%s\'' % item['command'])
        else:
            items.append(module.jsonify(item))

    return items


def main():
    argument_spec = dict(
        commands=dict(required=True),
        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(edgeos_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    warnings = list()
    result = {'changed': False}
    commands = parse_commands(module, warnings)
    wait_for = module.params['wait_for'] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as exc:
        module.fail_json(msg=to_text(exc))

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    for attempt in range(retries):
        responses = run_commands(module, commands)

        for item in conditionals:
            if item(responses):

                if match == 'any':
                    conditionals = list()
                    break

                conditionals.remove(item)

            if not conditionals:
                break

            time.sleep(interval)

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, falied_conditions=failed_conditions)

    result = {
        'changed': False,
        'stdout': responses,
        'warnings': warnings,
        'stdout_lines': list(to_lines(responses)),
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
