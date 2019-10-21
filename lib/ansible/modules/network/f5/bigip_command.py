#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_command
short_description: Run TMSH and BASH commands on F5 devices
description:
  - Sends a TMSH or BASH command to an BIG-IP node and returns the results
    read from the device. This module includes an argument that will cause
    the module to wait for a specific condition before returning or timing
    out if the condition is not met.
  - This module is B(not) idempotent, nor will it ever be. It is intended as
    a stop-gap measure to satisfy automation requirements until such a time as
    a real module has been developed to configure in the way you need.
  - If you are using this module, you should probably also be filing an issue
    to have a B(real) module created for your needs.
version_added: 2.4
options:
  commands:
    description:
      - The commands to send to the remote BIG-IP device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries as expired.
      - Only C(tmsh) commands are supported. If you are piping or adding additional
        logic that is outside of C(tmsh) (such as grep'ing, awk'ing or other shell
        related things that are not C(tmsh), this behavior is not supported.
    required: True
    type: raw
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward. If the conditional is not true
        by the configured retries, the task fails. See examples.
    type: list
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy. Valid
        values are C(all) or C(any). If the value is set to C(all)
        then all conditionals in the I(wait_for) must be satisfied. If
        the value is set to C(any) then only one of the values must be
        satisfied.
    type: str
    choices:
      - any
      - all
    default: all
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    type: int
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    type: int
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
    version_added: 2.5
  warn:
    description:
      - Whether the module should raise warnings related to command idempotency
        or not.
      - Note that the F5 Ansible developers specifically leave this on to make you
        aware that your usage of this module may be better served by official F5
        Ansible modules. This module should always be used as a last resort.
    default: True
    type: bool
    version_added: 2.6
  chdir:
    description:
      - Change into this directory before running the command.
    type: str
    version_added: 2.6
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: run show version on remote devices
  bigip_command:
    commands: show sys version
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost

- name: run show version and check to see if output contains BIG-IP
  bigip_command:
    commands: show sys version
    wait_for: result[0] contains BIG-IP
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  register: result
  delegate_to: localhost

- name: run multiple commands on remote nodes
  bigip_command:
    commands:
      - show sys version
      - list ltm virtual
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost

- name: run multiple commands and evaluate the output
  bigip_command:
    commands:
      - show sys version
      - list ltm virtual
    wait_for:
      - result[0] contains BIG-IP
      - result[1] contains my-vs
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  register: result
  delegate_to: localhost

- name: tmsh prefixes will automatically be handled
  bigip_command:
    commands:
      - show sys version
      - tmsh list ltm virtual
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost

- name: Delete all LTM nodes in Partition1, assuming no dependencies exist
  bigip_command:
    commands:
      - delete ltm node all
    chdir: Partition1
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
stdout:
  description: The set of responses from the commands.
  returned: always
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list.
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed.
  returned: failed
  type: list
  sample: ['...', '...']
warn:
  description: Whether or not to raise warnings about modification commands.
  returned: changed
  type: bool
  sample: True
'''

import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.parsing import FailedConditionsError
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import string_types
from collections import deque


try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import is_cli
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import is_cli

try:
    from ansible.module_utils.network.f5.common import run_commands
    HAS_CLI_TRANSPORT = True
except ImportError:
    HAS_CLI_TRANSPORT = False


class NoChangeReporter(object):
    stdout_re = [
        # A general error when a resource already exists
        re.compile(r"The requested.*already exists"),

        # Returned when creating a duplicate cli alias
        re.compile(r"Data Input Error: shared.*already exists"),
    ]

    def find_no_change(self, responses):
        """Searches the response for something that looks like a change

        This method borrows heavily from Ansible's ``_find_prompt`` method
        defined in the ``lib/ansible/plugins/connection/network_cli.py::Connection``
        class.

        Arguments:
            response (string): The output from the command.

        Returns:
            bool: True when change is detected. False otherwise.
        """
        for response in responses:
            for regex in self.stdout_re:
                if regex.search(response):
                    return True
        return False


class Parameters(AnsibleF5Parameters):
    returnables = ['stdout', 'stdout_lines', 'warnings', 'executed_commands']

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result

    @property
    def raw_commands(self):
        if self._values['commands'] is None:
            return []
        if isinstance(self._values['commands'], string_types):
            result = [self._values['commands']]
        else:
            result = self._values['commands']
        return result

    def convert_commands(self, commands):
        result = []
        for command in commands:
            tmp = dict(
                command='',
                pipeline=''
            )

            command = command.replace("'", "\\'")
            pipeline = command.split('|', 1)
            tmp['command'] = pipeline[0]
            try:
                tmp['pipeline'] = pipeline[1]
            except IndexError:
                pass
            result.append(tmp)
        return result

    def convert_commands_cli(self, commands):
        result = []
        for command in commands:
            tmp = dict(
                command='',
                pipeline=''
            )

            pipeline = command.split('|', 1)
            tmp['command'] = pipeline[0]
            try:
                tmp['pipeline'] = pipeline[1]
            except IndexError:
                pass
            result.append(tmp)
        return result

    def merge_command_dict(self, command):
        if command['pipeline'] != '':
            escape_patterns = r'([$"])'
            command['pipeline'] = re.sub(escape_patterns, r'\\\1', command['pipeline'])
            command['command'] = '{0} | {1}'.format(command['command'], command['pipeline']).strip()

    def merge_command_dict_cli(self, command):
        if command['pipeline'] != '':
            command['command'] = '{0} | {1}'.format(command['command'], command['pipeline']).strip()

    @property
    def rest_commands(self):
        # ['list ltm virtual']
        commands = self.normalized_commands
        commands = self.convert_commands(commands)
        if self.chdir:
            # ['cd /Common; list ltm virtual']
            for command in commands:
                self.addon_chdir(command)
        # ['tmsh -c "cd /Common; list ltm virtual"']
        for command in commands:
            self.addon_tmsh(command)
        for command in commands:
            self.merge_command_dict(command)
        result = [x['command'] for x in commands]
        return result

    @property
    def cli_commands(self):
        # ['list ltm virtual']
        commands = self.normalized_commands
        commands = self.convert_commands_cli(commands)
        if self.chdir:
            # ['cd /Common; list ltm virtual']
            for command in commands:
                self.addon_chdir(command)
        if not self.is_tmsh:
            # ['tmsh -c "cd /Common; list ltm virtual"']
            for command in commands:
                self.addon_tmsh_cli(command)
        for command in commands:
            self.merge_command_dict_cli(command)
        result = [x['command'] for x in commands]
        return result

    @property
    def normalized_commands(self):
        if self._values['normalized_commands'] is None:
            return None
        return deque(self._values['normalized_commands'])

    @property
    def chdir(self):
        if self._values['chdir'] is None:
            return None
        if self._values['chdir'].startswith('/'):
            return self._values['chdir']
        return '/{0}'.format(self._values['chdir'])

    @property
    def user_commands(self):
        commands = self.raw_commands
        return map(self._ensure_tmsh_prefix, commands)

    @property
    def wait_for(self):
        return self._values['wait_for'] or list()

    def addon_tmsh(self, command):
        escape_patterns = r'([$"])'
        if command['command'].count('"') % 2 != 0:
            raise Exception('Double quotes are unbalanced')
        command['command'] = re.sub(escape_patterns, r'\\\\\\\1', command['command'])
        command['command'] = 'tmsh -c \\\"{0}\\\"'.format(command['command'])

    def addon_tmsh_cli(self, command):
        if command['command'].count('"') % 2 != 0:
            raise Exception('Double quotes are unbalanced')
        command['command'] = 'tmsh -c "{0}"'.format(command['command'])

    def addon_chdir(self, command):
        command['command'] = "cd {0}; {1}".format(self.chdir, command['command'])


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = Parameters(params=self.module.params)
        self.want.update({'module': self.module})
        self.changes = Parameters(module=self.module)
        self.valid_configs = [
            'list', 'show', 'modify cli preference pager disabled'
        ]
        self.changed_command_prefixes = ('modify', 'create', 'delete')
        self.warnings = list()

    def _to_lines(self, stdout):
        lines = list()
        for item in stdout:
            if isinstance(item, string_types):
                item = item.split('\n')
            lines.append(item)
        return lines

    def exec_module(self):
        result = dict()

        changed = self.execute()

        result.update(**self.changes.to_return())
        result.update(dict(changed=changed))
        self._announce_warnings(result)
        return result

    def _announce_warnings(self, result):
        warnings = result.pop('warnings', [])
        for warning in warnings:
            self.module.warn(warning)

    def notify_non_idempotent_commands(self, commands):
        for index, item in enumerate(commands):
            if any(item.startswith(x) for x in self.valid_configs):
                return
            else:
                self.warnings.append(
                    'Using "write" commands is not idempotent. You should use '
                    'a module that is specifically made for that. If such a '
                    'module does not exist, then please file a bug. The command '
                    'in question is "{0}..."'.format(item[0:40])
                )

    @staticmethod
    def normalize_commands(raw_commands):
        if not raw_commands:
            return None
        result = []
        for command in raw_commands:
            command = command.strip()
            if command[0:5] == 'tmsh ':
                command = command[4:].strip()
            result.append(command)
        return result

    def parse_commands(self):
        results = []
        commands = self._transform_to_complex_commands(self.commands)

        for index, item in enumerate(commands):
            # This needs to be removed so that the ComplexList used in to_commands
            # will work correctly.
            output = item.pop('output', None)

            if output == 'one-line' and 'one-line' not in item['command']:
                item['command'] += ' one-line'
            elif output == 'text' and 'one-line' in item['command']:
                item['command'] = item['command'].replace('one-line', '')

            results.append(item)
        return results

    def execute(self):
        if self.want.normalized_commands:
            result = self.want.normalized_commands
        else:
            result = self.normalize_commands(self.want.raw_commands)
            self.want.update({'normalized_commands': result})
        if not result:
            return False
        self.notify_non_idempotent_commands(self.want.normalized_commands)

        commands = self.parse_commands()
        retries = self.want.retries
        conditionals = [Conditional(c) for c in self.want.wait_for]

        if self.module.check_mode:
            return

        while retries > 0:
            responses = self._execute(commands)
            self._check_known_errors(responses)
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
            errmsg = 'One or more conditional statements have not been satisfied.'
            raise FailedConditionsError(errmsg, failed_conditions)
        stdout_lines = self._to_lines(responses)
        changes = {
            'stdout': responses,
            'stdout_lines': stdout_lines,
            'executed_commands': self.commands
        }
        if self.want.warn:
            changes['warnings'] = self.warnings
        self.changes = Parameters(params=changes, module=self.module)
        return self.determine_change(responses)

    def determine_change(self, responses):
        changer = NoChangeReporter()
        if changer.find_no_change(responses):
            return False
        if any(x for x in self.want.normalized_commands if x.startswith(self.changed_command_prefixes)):
            return True
        return False

    def _check_known_errors(self, responses):
        # A regex to match the error IDs used in the F5 v2 logging framework.
        # pattern = r'^[0-9A-Fa-f]+:?\d+?:'

        for resp in responses:
            if 'usage: tmsh' in resp:
                raise F5ModuleError(
                    "tmsh command printed its 'help' message instead of running your command. "
                    "This usually indicates unbalanced quotes."
                )

    def _transform_to_complex_commands(self, commands):
        spec = dict(
            command=dict(key=True),
            output=dict(
                default='text',
                choices=['text', 'one-line']
            ),
        )
        transform = ComplexList(spec, self.module)
        result = transform(commands)
        return result


class V1Manager(BaseManager):
    """Supports CLI (SSH) communication with the remote device

    """
    def _execute(self, commands):
        if self.want.is_tmsh:
            command = dict(
                command="modify cli preference pager disabled"
            )
        else:
            command = dict(
                command="tmsh modify cli preference pager disabled"
            )
        self.execute_on_device(command)
        return self.execute_on_device(commands)

    @property
    def commands(self):
        return self.want.cli_commands

    def is_tmsh(self):
        try:
            self.execute_on_device('tmsh -v')
        except Exception as ex:
            if 'Syntax Error:' in str(ex):
                return True
            raise
        return False

    def execute(self):
        self.want.update({'is_tmsh': self.is_tmsh()})
        return super(V1Manager, self).execute()

    def execute_on_device(self, commands):
        result = run_commands(self.module, commands)
        return result


class V2Manager(BaseManager):
    """Supports REST communication with the remote device

    """
    def _execute(self, commands):
        command = dict(
            command="tmsh modify cli preference pager disabled"
        )
        self.execute_on_device(command)
        return self.execute_on_device(commands)

    @property
    def commands(self):
        return self.want.rest_commands

    def execute_on_device(self, commands):
        responses = []
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        for item in to_list(commands):
            try:
                args = dict(
                    command='run',
                    utilCmdArgs='-c "{0}"'.format(item['command'])
                )
                resp = self.client.api.post(uri, json=args)
                response = resp.json()
                if 'commandResult' in response:
                    output = u'{0}'.format(response['commandResult'])
                    responses.append(output.strip())
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
        return responses


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.module = kwargs.get('module', None)

    def exec_module(self):
        if is_cli(self.module) and HAS_CLI_TRANSPORT:
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        result = manager.exec_module()
        return result

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)


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
            ),
            warn=dict(
                type='bool',
                default='yes'
            ),
            chdir=dict()
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
