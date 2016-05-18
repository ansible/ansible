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
module: junos_command
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Execute arbitrary commands on a remote device running Junos
description:
  - Network devices running the Junos operating system provide a command
    driven interface both over CLI and RPC.  This module provides an
    interface to execute commands using these functions and return the
    results to the Ansible playbook.  In addition, the M(junos_command)
    module can specify a set of conditionals to be evaluated against the
    returned output, only returning control to the playbook once the
    entire set of conditionals has been met.
extends_documentation_fragment: junos
options:
  commands:
    description:
      - An ordered set of CLI commands to be executed on the remote
        device.  The output from the commands is then returned to
        the playbook in the task results.
    required: false
    default: null
  rpcs:
    description:
      - The C(rpcs) argument accepts a list of RPCs to be executed
        over a netconf session and the results from the RPC execution
        is return to the playbook via the modules results dictionary.
    required: false
    default: null
  waitfor:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional or set of
        considitonals to be true before moving forward.   If the
        conditional is not true by the configured retries, the
        task fails.  See examples.
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
  format:
    description:
      - Configures the encoding scheme to use when serializing output
        from the device.  This handles how to properly understand the
        output and apply the conditionals path to the result set.
    required: false
    default: 'xml'
    choices: ['xml', 'text']
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
# the required set of connection arguments have been purposely left off
# the examples for brevity

- name: run a set of commands
  junos_command:
    commands: ['show version', 'show ip route']

- name: run a command with a conditional applied to the second command
  junos_command:
    commands:
      - show version
      - show interfaces fxp0
    waitfor:
      - "result[1].interface-information.physical-interface.name eq fxp0"

- name: collect interface information using rpc
  junos_command:
    rpcs:
      - "get_interface_information interface=em0 media=True"
      - "get_interface_information interface=fxp0 media=True"
"""

RETURN = """
stdout:
  description: The output from the commands read from the device
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The output read from the device split into lines
  returned: always
  type: list
  sample: [['...', '...'], ['...', '...']]

xml:
  description: The raw XML reply from the device
  returned: when format is xml
  type: list
  sample: [['...', '...'], ['...', '...']]

failed_conditionals:
  description: the conditionals that failed
  retured: failed
  type: list
  sample: ['...', '...']
"""
import shlex

def split(value):
    lex = shlex.shlex(value)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

def rpc_args(args):
    kwargs = dict()
    args = split(args)
    name = args.pop(0)
    for arg in args:
        key, value = arg.split('=')
        if str(value).upper() in ['TRUE', 'FALSE']:
            kwargs[key] = bool(value)
        elif re.match(r'\d+', value):
            kwargs[key] = int(value)
        else:
            kwargs[key] = str(value)
    return (name, kwargs)

def parse_rpcs(rpcs):
    parsed = list()
    for rpc in (rpcs or list()):
        parsed.append(rpc_args(rpc))
    return parsed

def run_rpcs(module, items, format):
    response = list()
    for name, kwargs in items:
        kwargs['format'] = format
        result = module.connection.rpc(name, **kwargs)
        if format == 'text':
            response.append(result.text)
        else:
            response.append(result)
    return response

def iterlines(stdout):
    for item in stdout:
        if isinstance(item, basestring):
            item = str(item).split('\n')
        yield item

def main():
    """main entry point for Ansible module
    """

    spec = dict(
        commands=dict(type='list'),
        rpcs=dict(type='list'),
        format=dict(default='xml', choices=['text', 'xml']),
        waitfor=dict(type='list'),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),
        transport=dict(default='netconf', choices=['netconf'])
    )

    mutually_exclusive = [('commands', 'rpcs')]

    module = get_module(argument_spec=spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)


    commands = module.params['commands']
    rpcs = parse_rpcs(module.params['rpcs'])

    encoding = module.params['format']
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
        if commands:
            response = module.run_commands(commands, format=encoding)
        else:
            response = run_rpcs(module, rpcs, format=encoding)

        result['stdout'] = response
        xmlout = list()

        for index in range(0, len(response)):
            if encoding == 'xml':
                xmlout.append(xml_to_string(response[index]))
                response[index] = xml_to_json(response[index])

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

    if xmlout:
        result['xml'] = xmlout

    result['stdout_lines'] = list(iterlines(result['stdout']))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.junos import *

if __name__ == '__main__':
    main()

