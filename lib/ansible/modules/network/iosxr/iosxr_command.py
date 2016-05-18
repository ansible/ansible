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
module: iosxr_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on ios devices.
description:
  - Sends arbitrary commands to an IOSXR node and returns the results
    read from the device. The M(iosxr_command) module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: iosxr
options:
  commands:
    description:
      - List of commands to send to the remote ios device over the
        configured provider. The resulting output from the command
        is returned. If the I(waitfor) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retires as expired.
    required: true
  waitfor:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for a each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    required: false
    default: null
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        waitfor conditions.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    required: false
    default: 1
"""

EXAMPLES = """

- iosxr_command:
    commands:
      - show version
  register: output

- iosxr_command:
    commands:
      - show version
    waitfor:
      - "result[0] contains 6.0.0"

- iosxr_command:
  commands:
    - show version
    - show interfaces
  waitfor:
    - "result[1] contains MgmtEth0/0/CPU0/0"
    - "result[0] contains 6.0.0"

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
    except AttributeError:
        exc = get_exception()
        module.fail_json(msg=exc.message)


    result = dict(changed=False)

    while retries > 0:
        response = module.execute(commands)
        result['stdout'] = response

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
from ansible.module_utils.iosxr import *
if __name__ == '__main__':
        main()

