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
import collections
import itertools
import shlex

from ansible.module_utils.basic import BOOLEANS_TRUE, BOOLEANS_FALSE

DEFAULT_COMMENT_TOKENS = ['#', '!']

class ConfigLine(object):

    def __init__(self, text):
        self.text = text
        self.children = list()
        self.parents = list()
        self.raw = None

    def __str__(self):
        return self.raw

    def __eq__(self, other):
        if self.text == other.text:
            return self.parents == other.parents

    def __ne__(self, other):
        return not self.__eq__(other)

def ignore_line(text, tokens=None):
    for item in (tokens or DEFAULT_COMMENT_TOKENS):
        if text.startswith(item):
            return True

def parse(lines, indent, comment_tokens=None):
    toplevel = re.compile(r'\S')
    childline = re.compile(r'^\s*(.+)$')
    repl = r'([{|}|;])'

    ancestors = list()
    config = list()

    for line in str(lines).split('\n'):
        text = str(re.sub(repl, '', line)).strip()

        cfg = ConfigLine(text)
        cfg.raw = line

        if not text or ignore_line(text, comment_tokens):
            continue

        # handle top level commands
        if toplevel.match(line):
            ancestors = [cfg]

        # handle sub level commands
        else:
            match = childline.match(line)
            line_indent = match.start(1)
            level = int(line_indent / indent)
            parent_level = level - 1

            cfg.parents = ancestors[:level]

            if level > len(ancestors):
                config.append(cfg)
                continue

            for i in range(level, len(ancestors)):
                ancestors.pop()

            ancestors.append(cfg)
            ancestors[parent_level].children.append(cfg)

        config.append(cfg)

    return config


class NetworkConfig(object):

    def __init__(self, indent=None, contents=None, device_os=None):
        self.indent = indent or 1
        self._config = list()
        self._device_os = device_os

        if contents:
            self.load(contents)

    @property
    def items(self):
        return self._config

    def __str__(self):
        config = collections.OrderedDict()
        for item in self._config:
            self.expand(item, config)
        return '\n'.join(self.flatten(config))

    def load(self, contents):
        self._config = parse(contents, indent=self.indent)

    def load_from_file(self, filename):
        self.load(open(filename).read())

    def get(self, path):
        if isinstance(path, basestring):
            path = [path]
        for item in self._config:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def search(self, regexp, path=None):
        regex = re.compile(r'^%s' % regexp, re.M)

        if path:
            parent = self.get(path)
            if not parent or not parent.children:
                return
            children = [c.text for c in parent.children]
            data = '\n'.join(children)
        else:
            data = str(self)

        match = regex.search(data)
        if match:
            if match.groups():
                values = match.groupdict().values()
                groups = list(set(match.groups()).difference(values))
                return (groups, match.groupdict())
            else:
                return match.group()

    def findall(self, regexp):
        regexp = r'%s' % regexp
        return re.findall(regexp, str(self))

    def expand(self, obj, items):
        block = [item.raw for item in obj.parents]
        block.append(obj.raw)

        current_level = items
        for b in block:
            if b not in current_level:
                current_level[b] = collections.OrderedDict()
            current_level = current_level[b]
        for c in obj.children:
            if c.raw not in current_level:
                current_level[c.raw] = collections.OrderedDict()

    def flatten(self, data, obj=None):
        if obj is None:
            obj = list()
        for k, v in data.items():
            obj.append(k)
            self.flatten(v, obj)
        return obj

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def get_children(self, path):
        obj = self.get_object(path)
        if obj:
            return obj.children

    def difference(self, other, path=None, match='line', replace='line'):
        updates = list()

        config = self.items
        if path:
            config = self.get_children(path) or list()

        if match == 'line':
            for item in config:
                if item not in other.items:
                    updates.append(item)

        elif match == 'strict':
            if path:
                current = other.get_children(path) or list()
            else:
                current = other.items

            for index, item in enumerate(config):
                try:
                    if item != current[index]:
                        updates.append(item)
                except IndexError:
                    updates.append(item)

        elif match == 'exact':
            if path:
                current = other.get_children(path) or list()
            else:
                current = other.items

            if len(current) != len(config):
                updates.extend(config)
            else:
                for ours, theirs in itertools.izip(config, current):
                    if ours != theirs:
                        updates.extend(config)
                        break

        if self._device_os == 'junos':
            return updates

        diffs = dict()
        for update in updates:
            if replace == 'block' and update.parents:
                update = update.parents[-1]
            self.expand(update, diffs)

        return self.flatten(diffs)

    def _build_children(self, children, parents=None, offset=0):
        for item in children:
            line = ConfigLine(item)
            line.raw = item.rjust(len(item) + offset)
            if parents:
                line.parents = parents
                parents[-1].children.append(line)
            yield line

    def add(self, lines, parents=None):
        offset = 0

        config = list()
        parent = None
        parents = parents or list()

        for item in parents:
            line = ConfigLine(item)
            line.raw = item.rjust(len(item) + offset)
            config.append(line)
            if parent:
                parent.children.append(line)
                line.parents.append(parent)
            parent = line
            offset += self.indent

        self._config.extend(config)
        self._config.extend(list(self._build_children(lines, config, offset)))



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
        'contains': ['contains']
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
        return self.value in value




