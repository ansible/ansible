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
author: "Peter sprygada (@privateip)"
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
  waitfor:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward.   If the conditional is not true
        by the configured retries, the task fails.  See examples.
    required: false
    default: null
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
    commands: "{{ lookup('file', 'commands.txt') }}"

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

import time
import shlex
import re

INDEX_RE = re.compile(r'(\[\d+\])')

def iterlines(stdout):
    for item in stdout:
        if isinstance(item, basestring):
            item = str(item).split('\n')
        yield item

def main():
    spec = dict(
        commands=dict(type='list'),
        waitfor=dict(type='list'),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)

    commands = module.params['commands']

    retries = module.params['retries']
    interval = module.params['interval']

    try:
        queue = set()
        for entry in (module.params['waitfor'] or list()):
            queue.add(Conditional(entry))
    except AttributeError, exc:
        module.fail_json(msg=exc.message)

    result = dict(changed=False)

    while retries > 0:
        response = module.execute(commands)
        result['stdout'] = response

        for index, cmd in enumerate(commands):
            if cmd.endswith('json'):
                response[index] = module.from_json(response[index])

        for item in list(queue):
            if item(response):
                queue.remove(item)

        if not queue:
            break

        time.sleep(interval)
        retries -= 1
    else:
        failed_conditions = [item.raw for item in queue]
        module.fail_json(msg='timeout waiting for value', failed_conditions=failed_conditions)

    result['stdout_lines'] = list(iterlines(result['stdout']))
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.eos import *
if __name__ == '__main__':
        main()

