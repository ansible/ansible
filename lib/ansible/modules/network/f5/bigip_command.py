#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_command
short_description: Run arbitrary command on F5 devices
description:
  - Sends an arbitrary command to an BIG-IP node and returns the results
    read from the device. This module includes an argument that will cause
    the module to wait for a specific condition before returning or timing
    out if the condition is not met.
version_added: "2.4"
options:
  commands:
    description:
      - The commands to send to the remote BIG-IP device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries as expired.
      - The I(commands) argument also accepts an alternative form
        that allows for complex values that specify the command
        to run and the output format to return. This can be done
        on a command by command basis. The complex argument supports
        the keywords C(command) and C(output) where C(command) is the
        command to run and C(output) is 'text' or 'one-line'.
    required: True
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward. If the conditional is not true
        by the configured retries, the task fails. See examples.
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy. Valid
        values are C(all) or C(any). If the value is set to C(all)
        then all conditionals in the I(wait_for) must be satisfied. If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    default: 1
  transport:
    description:
      - Configures the transport connection to use when connecting to the
        remote device. The transport argument supports connectivity to the
        device over cli (ssh) or rest.
    required: true
    choices:
        - rest
        - cli
    default: rest
    version_added: "2.5"
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: run show version on remote devices
  bigip_command:
    commands: show sys version
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: run show version and check to see if output contains BIG-IP
  bigip_command:
    commands: show sys version
    wait_for: result[0] contains BIG-IP
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: run multiple commands on remote nodes
  bigip_command:
    commands:
      - show sys version
      - list ltm virtual
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: run multiple commands and evaluate the output
  bigip_command:
    commands:
      - show sys version
      - list ltm virtual
    wait_for:
      - result[0] contains BIG-IP
      - result[1] contains my-vs
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: tmsh prefixes will automatically be handled
  bigip_command:
    commands:
      - show sys version
      - tmsh list ltm virtual
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
stdout:
  description: The set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
'''

import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.network.common.parsing import FailedConditionsError
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.utils import to_list
from collections import deque

HAS_DEVEL_IMPORTS = False

try:
    # Sideband repository used for dev
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fqdn_name
    from library.module_utils.network.f5.common import is_cli
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
    HAS_DEVEL_IMPORTS = True
    try:
        from library.module_utils.network.f5.common import run_commands
        HAS_CLI_TRANSPORT = True
    except ImportError:
        HAS_CLI_TRANSPORT = False
except ImportError:
    # Upstream Ansible
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fqdn_name
    from ansible.module_utils.network.f5.common import is_cli
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
    try:
        from ansible.module_utils.network.f5.common import run_commands
        HAS_CLI_TRANSPORT = True
    except ImportError:
        HAS_CLI_TRANSPORT = False


class Parameters(AnsibleF5Parameters):
    returnables = ['stdout', 'stdout_lines', 'warnings']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def _listify(self, item):
        if isinstance(item, string_types):
            result = [item]
        else:
            result = item
        return result

    @property
    def commands(self):
        commands = self._listify(self._values['commands'])
        commands = deque(commands)
        if not is_cli(self.module):
            commands.appendleft(
                'tmsh modify cli preference pager disabled'
            )
        commands = map(self._ensure_tmsh_prefix, list(commands))
        return list(commands)

    @property
    def user_commands(self):
        commands = self._listify(self._values['commands'])
        return map(self._ensure_tmsh_prefix, commands)

    def _ensure_tmsh_prefix(self, cmd):
        cmd = cmd.strip()
        if cmd[0:5] != 'tmsh ':
            cmd = 'tmsh ' + cmd.strip()
        return cmd


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(params=self.module.params)
        self.want.update({'module': self.module})
        self.changes = Parameters(module=self.module)

    def _to_lines(self, stdout):
        lines = list()
        for item in stdout:
            if isinstance(item, string_types):
                item = str(item).split('\n')
            lines.append(item)
        return lines

    def _is_valid_mode(self, cmd):
        valid_configs = [
            'list', 'show',
            'modify cli preference pager disabled'
        ]
        if not is_cli(self.module):
            valid_configs = list(map(self.want._ensure_tmsh_prefix, valid_configs))
        if any(cmd.startswith(x) for x in valid_configs):
            return True
        return False

    def is_tmsh(self):
        try:
            self._run_commands(self.module, 'tmsh help')
        except F5ModuleError as ex:
            if 'Syntax Error:' in str(ex):
                return True
            raise
        return False

    def exec_module(self):
        result = dict()

        try:
            changed = self.execute()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.changes.to_return())
        result.update(dict(changed=changed))
        return result

    def _run_commands(self, module, commands):
        return run_commands(module, commands)

    def execute(self):
        warnings = list()
        changed = ('tmsh modify', 'tmsh create', 'tmsh delete')
        commands = self.parse_commands(warnings)
        wait_for = self.want.wait_for or list()
        retries = self.want.retries
        conditionals = [Conditional(c) for c in wait_for]

        if self.module.check_mode:
            return

        while retries > 0:
            if is_cli(self.module) and HAS_CLI_TRANSPORT:
                if self.is_tmsh():
                    for command in commands:
                        command['command'] = command['command'][4:].strip()
                responses = self._run_commands(self.module, commands)
            else:
                responses = self.execute_on_device(commands)

            for item in list(conditionals):
                if item(responses):
                    if self.want.match == 'any':
                        conditionals = list()
                        break
                    conditionals.remove(item)

            if not conditionals:
                break

            time.sleep(self.want.interval)
            retries -= 1
        else:
            failed_conditions = [item.raw for item in conditionals]
            errmsg = 'One or more conditional statements have not been satisfied'
            raise FailedConditionsError(errmsg, failed_conditions)

        changes = {
            'stdout': responses,
            'stdout_lines': self._to_lines(responses),
            'warnings': warnings
        }
        self.changes = Parameters(params=changes, module=self.module)
        if any(x for x in self.want.user_commands if x.startswith(changed)):
            return True
        return False

    def parse_commands(self, warnings):
        results = []
        commands = list(deque(set(self.want.commands)))
        spec = dict(
            command=dict(key=True),
            output=dict(
                default='text',
                choices=['text', 'one-line']
            ),
        )

        transform = ComplexList(spec, self.module)
        commands = transform(commands)

        for index, item in enumerate(commands):
            if not self._is_valid_mode(item['command']) and is_cli(self.module):
                warnings.append(
                    'Using "write" commands is not idempotent. You should use '
                    'a module that is specifically made for that. If such a '
                    'module does not exist, then please file a bug. The command '
                    'in question is "%s..."' % item['command'][0:40]
                )
            # This needs to be removed so that the ComplexList used in to_commands
            # will work correctly.
            output = item.pop('output', None)

            if output == 'one-line' and 'one-line' not in item['command']:
                item['command'] += ' one-line'
            elif output == 'text' and 'one-line' in item['command']:
                item['command'] = item['command'].replace('one-line', '')

            results.append(item)
        return results

    def execute_on_device(self, commands):
        responses = []
        escape_patterns = r'([$' + "'])"
        for item in to_list(commands):
            command = re.sub(escape_patterns, r'\\\1', item['command'])
            output = self.client.api.tm.util.bash.exec_cmd(
                'run',
                utilCmdArgs='-c "{0}"'.format(command)
            )
            if hasattr(output, 'commandResult'):
                responses.append(str(output.commandResult))
        return responses


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            commands=dict(
                type='raw',
                required=True
            ),
            wait_for=dict(
                type='list',
                aliases=['waitfor']
            ),
            match=dict(
                default='all',
                choices=['any', 'all']
            ),
            retries=dict(
                default=10,
                type='int'
            ),
            interval=dict(
                default=1,
                type='int'
            ),
            transport=dict(
                type='str',
                default='rest',
                choices=['cli', 'rest']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if is_cli(module) and not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required to use the rest api")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
