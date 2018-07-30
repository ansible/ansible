#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Run arbitrary commands on an Juniper JUNOS device
description:
  - Sends an arbitrary set of commands to an JUNOS node and returns the results
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
  rpcs:
    description:
      - The C(rpcs) argument accepts a list of RPCs to be executed
        over a netconf session and the results from the RPC execution
        is return to the playbook via the modules results dictionary.
    version_added: "2.3"
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward.   If the conditional is not true
        by the configured retries, the task fails.  See examples.
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
    default: all
    choices: ['any', 'all']
    version_added: "2.2"
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command.  If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    default: 1
  display:
    description:
      - Encoding scheme to use when serializing output from the device.
        This handles how to properly understand the output and apply the
        conditionals path to the result set. For I(rpcs) argument default
        display is C(xml) and for I(commands) argument default display
        is C(text). Value C(set) is applicable only for fetching configuration
        from device.
    default: depends on input argument I(rpcs) or I(commands)
    aliases: ['format', 'output']
    choices: ['text', 'json', 'xml', 'set']
    version_added: "2.3"
requirements:
  - jxmlease
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(network_cli) connections and with C(local) connections for legacy playbooks.
"""

EXAMPLES = """
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
    commands: show version
    display: json

- name: run rpc on the remote device
  junos_command:
    commands: show configuration
    display: set

- name: run rpc on the remote device
  junos_command:
    rpcs: get-software-information
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
output:
  description: The set of transformed xml to json format from the commands responses
  returned: If the I(display) is in C(xml) format.
  type: list
  sample: ['...', '...']
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import time
import re
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.netconf import exec_rpc
from ansible.module_utils.network.junos.junos import junos_argument_spec, get_configuration, get_connection, get_capabilities, tostring
from ansible.module_utils.network.common.parsing import Conditional, FailedConditionalError
from ansible.module_utils.six import string_types, iteritems


try:
    from lxml.etree import Element, SubElement
except ImportError:
    from xml.etree.ElementTree import Element, SubElement

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

USE_PERSISTENT_CONNECTION = True


def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        lines.append(item)
    return lines


def rpc(module, items):

    responses = list()
    for item in items:
        name = item['name']
        xattrs = item['xattrs']
        fetch_config = False

        args = item.get('args')
        text = item.get('text')

        name = str(name).replace('_', '-')

        if all((module.check_mode, not name.startswith('get'))):
            module.fail_json(msg='invalid rpc for running in check_mode')

        if name == 'command' and text.startswith('show configuration') or name == 'get-configuration':
            fetch_config = True

        element = Element(name, xattrs)

        if text:
            element.text = text

        elif args:
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

        if fetch_config:
            reply = get_configuration(module, format=xattrs['format'])
        else:
            reply = exec_rpc(module, tostring(element), ignore_warning=False)

        if xattrs['format'] == 'text':
            if fetch_config:
                data = reply.find('.//configuration-text')
            else:
                data = reply.find('.//output')

            if data is None:
                module.fail_json(msg=tostring(reply))

            responses.append(data.text.strip())

        elif xattrs['format'] == 'json':
            responses.append(module.from_json(reply.text.strip()))

        elif xattrs['format'] == 'set':
            data = reply.find('.//configuration-set')
            if data is None:
                module.fail_json(msg="Display format 'set' is not supported by remote device.")
            responses.append(data.text.strip())

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

    for rpc in (module.params['rpcs'] or list()):
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

        display = module.params['display'] or 'xml'

        if display == 'set' and rpc != 'get-configuration':
            module.fail_json(msg="Invalid display option '%s' given for rpc '%s'" % ('set', name))

        xattrs = {'format': display}
        items.append({'name': name, 'args': args, 'xattrs': xattrs})

    return items


def parse_commands(module, warnings):
    items = list()

    for command in (module.params['commands'] or list()):
        if module.check_mode and not command.startswith('show'):
            warnings.append(
                'Only show commands are supported when using check_mode, not '
                'executing %s' % command
            )
            continue

        parts = command.split('|')
        text = parts[0]

        display = module.params['display'] or 'text'

        if '| display json' in command:
            display = 'json'

        elif '| display xml' in command:
            display = 'xml'

        if display == 'set' or '| display set' in command:
            if command.startswith('show configuration'):
                display = 'set'
            else:
                module.fail_json(msg="Invalid display option '%s' given for command '%s'" % ('set', command))

        xattrs = {'format': display}
        items.append({'name': 'command', 'xattrs': xattrs, 'text': text})

    return items


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list'),
        rpcs=dict(type='list'),

        display=dict(choices=['text', 'json', 'xml', 'set'], aliases=['format', 'output']),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(junos_argument_spec)

    required_one_of = [('commands', 'rpcs')]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    warnings = list()
    conn = get_connection(module)
    capabilities = get_capabilities(module)

    if capabilities.get('network_api') == 'cliconf':
        if any((module.params['wait_for'], module.params['match'], module.params['rpcs'])):
            module.warn('arguments wait_for, match, rpcs are not supported when using transport=cli')
        commands = module.params['commands']

        output = list()
        display = module.params['display']
        for cmd in commands:
            # if display format is not mentioned in command, add the display format
            # from the modules params
            if ('display json' not in cmd) and ('display xml' not in cmd):
                if display and display != 'text':
                    cmd += ' | display {0}'.format(display)
            try:
                output.append(conn.get(command=cmd))
            except ConnectionError as exc:
                module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        lines = [out.split('\n') for out in output]
        result = {'changed': False, 'stdout': output, 'stdout_lines': lines}
        module.exit_json(**result)

    items = list()
    items.extend(parse_commands(module, warnings))
    items.extend(parse_rpcs(module))

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        responses = rpc(module, items)
        transformed = list()
        output = list()
        for item, resp in zip(items, responses):
            if item['xattrs']['format'] == 'xml':
                if not HAS_JXMLEASE:
                    module.fail_json(msg='jxmlease is required but does not appear to be installed. '
                                         'It can be installed using `pip install jxmlease`')

                try:
                    json_resp = jxmlease.parse(resp)
                    transformed.append(json_resp)
                    output.append(json_resp)
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
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result = {
        'changed': False,
        'warnings': warnings,
        'stdout': responses,
        'stdout_lines': to_lines(responses)
    }

    if output:
        result['output'] = output

    module.exit_json(**result)

if __name__ == '__main__':
    main()
