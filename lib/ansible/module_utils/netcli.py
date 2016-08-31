# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import re
import time
import itertools
import shlex

from ansible.module_utils.basic import BOOLEANS_TRUE, BOOLEANS_FALSE
from ansible.module_utils.six import string_types

def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()

class FailedConditionsError(Exception):
    def __init__(self, msg, failed_conditions):
        super(FailedConditionsError, self).__init__(msg)
        self.failed_conditions = failed_conditions

class AddCommandError(Exception):
    def __init__(self, msg, command):
        super(AddCommandError, self).__init__(msg)
        self.command = command

class Cli(object):

    def __init__(self, connection):
        self.connection = connection
        self.default_output = connection.default_output or 'text'
        self._commands = list()

    @property
    def commands(self):
        return [str(c) for c in self._commands]

    def __call__(self, commands, output=None):
        objects = list()
        for cmd in to_list(commands):
            objects.append(self.to_command(cmd, output))
        return self.connection.run_commands(objects)

    def to_command(self, command, output=None, prompt=None, response=None):
        output = output or self.default_output
        if isinstance(command, Command):
            return command
        elif isinstance(command, dict):
            output = cmd.get('output') or output
            cmd = cmd['command']
        if isinstance(prompt, string_types):
            prompt = re.compile(re.escape(prompt))
        return Command(command, output, prompt=prompt, response=response)

    def add_commands(self, commands, output=None, **kwargs):
        for cmd in commands:
            self._commands.append(self.to_command(cmd, output, **kwargs))

    def run_commands(self):
        responses = self.connection.run_commands(self._commands)
        for resp, cmd in itertools.izip(responses, self._commands):
            cmd.response = resp

        # wipe out the commands list to avoid issues if additional
        # commands are executed later
        self._commands = list()

        return responses

class Command(object):

    def __init__(self, command, output=None, prompt=None, is_reboot=False,
                 response=None, delay=0):

        self.command = command
        self.output = output
        self.command_string = command

        self.prompt = prompt
        self.response = response

        self.is_reboot = is_reboot
        self.delay = delay

    def __str__(self):
        return self.command_string

class CommandRunner(object):

    def __init__(self, module):
        self.module = module

        self.items = list()
        self.conditionals = set()

        self.commands = list()

        self.retries = 10
        self.interval = 1

        self.match = 'all'

        self._cache = dict()
        self._default_output = module.connection.default_output


    def add_command(self, command, output=None, prompt=None, response=None):
        if command in [str(c) for c in self.commands]:
            raise AddCommandError('duplicated command detected', command=command)
        cmd = self.module.cli.to_command(command, output=output, prompt=prompt,
                                         response=response)
        self.commands.append(cmd)

    def get_command(self, command, output=None):
        output = output or self._default_output
        try:
            cmdobj = self._cache[(command, output)]
            return cmdobj.response
        except KeyError:
            for cmd in self.commands:
                if cmd.command == command and cmd.output == output:
                    self._cache[(command, output)] = cmd
                    return cmd.response
        raise ValueError("command '%s' not found" % command)

    def get_responses(self):
        return [cmd.response for cmd in self.commands]

    def add_conditional(self, condition):
        self.conditionals.add(Conditional(condition))

    def run(self):
        while self.retries > 0:
            self.module.cli.add_commands(self.commands)
            responses = self.module.cli.run_commands()

            for item in list(self.conditionals):
                if item(responses):
                    if self.match == 'any':
                        return item
                    self.conditionals.remove(item)

            if not self.conditionals:
                break

            time.sleep(self.interval)
            self.retries -= 1
        else:
            failed_conditions = [item.raw for item in self.conditionals]
            errmsg = 'One or more conditional statements have not be satisfied'
            raise FailedConditionsError(errmsg, failed_conditions)

class Conditional(object):
    """Used in command modules to evaluate waitfor conditions
    """

    OPERATORS = {
        'eq': ['eq', '=='],
        'neq': ['neq', 'ne', '!='],
        'gt': ['gt', '>'],
        'ge': ['ge', '>='],
        'lt': ['lt', '<'],
        'le': ['le', '<='],
        'contains': ['contains'],
        'matches': ['matches']
    }

    def __init__(self, conditional, encoding='json'):
        self.raw = conditional
        self.encoding = encoding

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
        if self.encoding in ['json', 'text']:
            return self.get_json(result)
        elif self.encoding == 'xml':
            return self.get_xml(result.get('result'))

    def get_xml(self, result):
        parts = self.key.split('.')

        value_index = None
        match = re.match(r'^\S+(\[)(\d+)\]', parts[-1])
        if match:
            start, end = match.regs[1]
            parts[-1] = parts[-1][0:start]
            value_index = int(match.group(2))

        path = '/'.join(parts[1:])
        path = '/%s' % path
        path += '/text()'

        index = int(re.match(r'result\[(\d+)\]', parts[0]).group(1))
        values = result[index].xpath(path)

        if value_index is not None:
            return values[value_index].strip()
        return [v.strip() for v in values]

    def get_json(self, result):
        parts = re.split(r'\.(?=[^\]]*(?:\[|$))', self.key)
        for part in parts:
            match = re.findall(r'\[(\S+?)\]', part)
            if match:
                key = part[:part.find('[')]
                result = result[key]
                for m in match:
                    try:
                        m = int(m)
                    except ValueError:
                        m = str(m)
                    result = result[m]
            else:
                result = result.get(part)
        return result

    def number(self, value):
        if '.' in str(value):
            return float(value)
        else:
            return int(value)

    def eq(self, value):
        return value == self.value

    def neq(self, value):
        return value != self.value

    def gt(self, value):
        return self.number(value) > self.value

    def ge(self, value):
        return self.number(value) >= self.value

    def lt(self, value):
        return self.number(value) < self.value

    def le(self, value):
        return self.number(value) <= self.value

    def contains(self, value):
        return str(self.value) in value

    def matches(self, value):
        match = re.search(value, self.value, re.M)
        return match is not None

