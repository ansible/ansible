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
  - Sends an aribtrary command to and EOS node and returns the results
    read from the device.  The M(eos_command) modulule includes an
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
        the number of retires as expired.
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
      - Specifies the number of retries a command should by tried
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
      - show version
  register: output

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

result:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

failed_conditionals:
  description: the conditionals that failed
  retured: failed
  type: list
  sample: ['...', '...']

"""

import time
import shlex
import re
import json

INDEX_RE = re.compile(r'(\[\d+\])')

def get_response(data):
    try:
        json_data = json.loads(data)
    except ValueError:
        json_data = None
    return dict(data=data, json=json_data)

class Conditional(object):

    OPERATORS = {
        'eq': ['eq', '=='],
        'neq': ['neq', 'ne', '!='],
        'gt': ['gt', '>'],
        'ge': ['ge', '>='],
        'lt': ['lt', '<'],
        'le': ['le', '<='],
        'contains': ['contains', 'in']
    }

    def __init__(self, conditional):
        self.raw = conditional

        key, op, val = shlex.split(conditional)
        self.key = key
        self.func = self.func(op)
        self.value = self._cast_value(val)

    def __call__(self, data):
        value = self.get_value(dict(result=data))
        return self.func(value)

    def _cast_value(self, value):
        if value in BOOLEANS_TRUE:
            return True
        elif value in BOOLEANS_FALSE:
            return False
        elif re.match(r'^\d+\.d+$', value):
            return float(value)
        elif re.match(r'^\d+$', value):
            return int(value)
        else:
            return unicode(value)

    def func(self, oper):
        for func, operators in self.OPERATORS.items():
            if oper in operators:
                return getattr(self, func)
        raise AttributeError('unknown operator: %s' % oper)

    def get_value(self, result):
        for key in self.key.split('.'):
            match = re.match(r'^(\w+)\[(\d+)\]', key)
            if match:
                key, index = match.groups()
                result = result[key][int(index)]
            else:
                result = result.get(key)
        return result

    def eq(self, value):
        return value == self.value

    def neq(self, value):
        return value != self.value

    def gt(self, value):
        return value > self.value

    def ge(self, value):
        return value >= self.value

    def lt(self, value):
        return value < self.value

    def le(self, value):
        return value <= self.value

    def contains(self, value):
        return self.value in value

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

    result = dict(changed=False, result=list())

    while retries > 0:
        response = module.execute(commands)
        result['result'] = response

        for index, cmd in enumerate(commands):
            if cmd.endswith('json'):
                response[index] = json.loads(response[index])

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

    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.eos import *
if __name__ == '__main__':
        main()

