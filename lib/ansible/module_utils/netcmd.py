#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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

import re
import time
import itertools
import shlex

from ansible.module_utils.basic import BOOLEANS_TRUE, BOOLEANS_FALSE

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


class FailedConditionsError(Exception):

    def __init__(self, msg, failed_conditions):
        super(FailedConditionsError, self).__init__(msg)
        self.failed_conditions = failed_conditions

class CommandRunner(object):

    def __init__(self, module):
        self.module = module

        self.items = list()
        self.conditionals = set()

        self.retries = 10
        self.interval = 1

        self._cache = dict()

    def add_command(self, command, output=None):
        self.module.cli.add_commands(command, output=output)

    def get_command(self, command):
        try:
            cmdobj = self._cache[command]
            return cmdobj.response
        except KeyError:
            for cmd in self.module.cli.commands:
                if str(cmd) == command:
                    self._cache[command] = cmd
                    return cmd.response
        raise ValueError("command '%s' not found" % command)


    def add_conditional(self, condition):
        self.conditionals.add(Conditional(condition))

    def run_commands(self):
        responses = self.module.cli.run_commands()
        self.items = responses

    def run(self):
        while self.retries > 0:
            self.run_commands()

            for item in list(self.conditionals):
                if item(self.items):
                    self.conditionals.remove(item)

            if not self.conditionals:
                break

            time.sleep(self.interval)
            self.retries -= 1
        else:
            failed_conditions = [item.raw for item in self.conditionals]
            raise FailedConditionsError('timeout waiting for value', failed_conditions)

