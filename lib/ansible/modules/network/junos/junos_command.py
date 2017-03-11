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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'core',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: junos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on an Juniper junos device
description:
  - Sends an arbitrary set of commands to an junos node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
extends_documentation_fragment: junos
options:
  commands:
    description:
      - The commands to send to the remote junos device over the
        configured provider.  The resulting output from the command
        is returned.  If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of I(retries) has been exceeded.
    required: true
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
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(wait_for)
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
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
- name: run show version on remote devices
  junos_command:
    commands: show version

- name: run show version and check to see if output contains Juniper
  junos_command:
    commands: show version
    wait_for: result[0] contains Juniper

- name: run multiple commands on remote nodes
  junos_command:
    commands:
      - show version
      - show interfaces

- name: run multiple commands and evaluate the output
  junos_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Juniper
      - result[1] contains Loopback0

- name: run commands and specify the output format
  junos_command:
    commands:
      - command: show version
        output: json
"""

RETURN = """
failed_conditions:
  description: the conditionals that failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import time
import re
import shlex

from functools import partial
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, tostring


from ansible.module_utils.junos import run_commands
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcli import Conditional, FailedConditionalError
from ansible.module_utils.netconf import send_request
from ansible.module_utils.network_common import ComplexList, to_list
from ansible.module_utils.six import string_types, iteritems

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

USE_PERSISTENT_CONNECTION = True


VALID_KEYS = {
    'cli': frozenset(['command', 'output', 'prompt', 'response']),
    'rpc': frozenset(['command', 'output'])
}

def check_transport(module):
    transport = (module.params['provider'] or {}).get('transport')

    if transport == 'netconf' and not module.params['rpcs']:
        module.fail_json(msg='argument commands is only supported over cli transport')

    elif transport == 'cli' and not module.params['commands']:
        module.fail_json(msg='argument rpcs is only supported over netconf transport')

def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        lines.append(item)
    return lines

def run_rpcs(module, items):

    responses = list()

    for item in items:
        name = item['name']
        args = item['args']

        name = str(name).replace('_', '-')

        if all((module.check_mode, not name.startswith('get'))):
            module.fail_json(msg='invalid rpc for running in check_mode')

        xattrs = {'format': item['output']}

        element = Element(name, xattrs)

        for key, value in iteritems(args):
            key = str(key).replace('_', '-')
            if isinstance(value, list):
                for item in value:
                    child = SubElement(element, key)
                    if item is not True:
                        child.text = item
            else:
                child = SubElement(element, key)
                if value is not True:
                    child.text = value

        reply = send_request(module, element)

        if module.params['display'] == 'text':
            data = reply.find('.//output')
            responses.append(data.text.strip())
        elif module.params['display'] == 'json':
            responses.append(module.from_json(reply.text.strip()))
        else:
            responses.append(tostring(reply))

    return responses

def split(value):
    lex = shlex.shlex(value)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

def parse_rpcs(module):
    items = list()
    for rpc in module.params['rpcs']:
        parts = split(rpc)

        name = parts.pop(0)
        args = dict()

        for item in parts:
            key, value = item.split('=')
            if str(value).upper() in ['TRUE', 'FALSE']:
                args[key] = bool(value)
            elif re.match(r'^[0-9]+$', value):
                args[key] = int(value)
            else:
                args[key] = str(value)

        output = module.params['display'] or 'xml'
        items.append({'name': name, 'args': args, 'output': output})

    return items


def parse_commands(module):
    spec = dict(
        command=dict(key=True),
        output=dict(default=module.params['display'], choices=['text', 'json', 'xml']),
        prompt=dict(),
        answer=dict()
    )

    transform = ComplexList(spec, module)
    commands = transform(module.params['commands'])

    for index, item in enumerate(commands):
        if module.check_mode and not item['command'].startswith('show'):
            warnings.append(
                'Only show commands are supported when using check_mode, not '
                'executing %s' % item['command']
            )

        if item['command'].startswith('show configuration'):
            item['output'] = 'text'
        if item['output'] == 'json' and 'display json' not in item['command']:
            item['command'] += '| display json'
        elif item['output'] == 'xml' and 'display xml' not in item['command']:
            item['command'] += '| display xml'
        else:
            if '| display json' in item['command']:
                item['command'] = str(item['command']).replace(' | display json', '')
            elif '| display xml' in item['command']:
                item['command'] = str(item['command']).replace(' | display xml', '')
        commands[index] = item

    return commands

def main():
    """entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list'),
        rpcs=dict(type='list'),

        display=dict(choices=['text', 'json', 'xml'], aliases=['format', 'output']),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(junos_argument_spec)

    mutually_exclusive = [('commands', 'rpcs')]

    required_one_of = [('commands', 'rpcs')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    check_transport(module)

    warnings = list()
    check_args(module, warnings)

    if module.params['commands']:
        items = parse_commands(module)
    else:
        items = parse_rpcs(module)


    wait_for = module.params['wait_for'] or list()
    display = module.params['display']
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        if module.params['commands']:
            responses = run_commands(module, items)
        else:
            responses = run_rpcs(module, items)

        transformed = list()

        for item, resp in zip(items, responses):
            if item['output'] == 'xml':
                if not HAS_JXMLEASE:
                    module.fail_json(msg='jxmlease is required but does not appear to '
                        'be installed.  It can be installed using `pip install jxmlease`')

                try:
                    transformed.append(jxmlease.parse(resp))
                except:
                    raise ValueError(resp)
            else:
                transformed.append(resp)

        for item in list(conditionals):
            try:
                if item(transformed):
                    if match == 'any':
                        conditionals = list()
                        break
                    conditionals.remove(item)
            except FailedConditionalError:
                pass

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not be satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result = {
        'changed': False,
        'warnings': warnings,
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    }


    module.exit_json(**result)


if __name__ == '__main__':
    main()
