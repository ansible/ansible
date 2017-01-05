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

import itertools
import re

from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import zip, zip_longest

DEFAULT_COMMENT_TOKENS = ['#', '!', '/*', '*/']


def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


class Config(object):

    def __init__(self, connection):
        self.connection = connection

    def __call__(self, commands, **kwargs):
        lines = to_list(commands)
        return self.connection.configure(lines, **kwargs)

    def load_config(self, commands, **kwargs):
        commands = to_list(commands)
        return self.connection.load_config(commands, **kwargs)

    def get_config(self, **kwargs):
        return self.connection.get_config(**kwargs)

    def save_config(self):
        return self.connection.save_config()

class ConfigLine(object):

    def __init__(self, text):
        self.text = text
        self.children = list()
        self.parents = list()
        self.raw = None

    @property
    def line(self):
        line = [p.text for p in self.parents]
        line.append(self.text)
        return ' '.join(line)

    def __str__(self):
        return self.raw

    def __eq__(self, other):
        return self.line == other.line

    def __ne__(self, other):
        return not self.__eq__(other)

def ignore_line(text, tokens=None):
    for item in (tokens or DEFAULT_COMMENT_TOKENS):
        if text.startswith(item):
            return True

def get_next(iterable):
    item, next_item = itertools.tee(iterable, 2)
    next_item = itertools.islice(next_item, 1, None)
    return zip_longest(item, next_item)

def parse(lines, indent, comment_tokens=None):
    toplevel = re.compile(r'\S')
    childline = re.compile(r'^\s*(.+)$')

    ancestors = list()
    config = list()

    for line in str(lines).split('\n'):
        text = str(re.sub(r'([{};])', '', line)).strip()

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

def dumps(objects, output='block'):
    if output == 'block':
        items = [c.raw for c in objects]
    elif output == 'commands':
        items = [c.text for c in objects]
    elif output == 'lines':
        items = list()
        for obj in objects:
            line = list()
            line.extend([p.text for p in obj.parents])
            line.append(obj.text)
            items.append(' '.join(line))
    else:
        raise TypeError('unknown value supplied for keyword output')
    return '\n'.join(items)

class NetworkConfig(object):

    def __init__(self, indent=None, contents=None, device_os=None):
        self.indent = indent or 1
        self._config = list()
        self._device_os = device_os
        self._syntax = 'block' # block, lines, junos

        if self._device_os == 'junos':
            self._syntax = 'junos'

        if contents:
            self.load(contents)

    @property
    def items(self):
        return self._config

    def __str__(self):
        if self._device_os == 'junos':
            return dumps(self.expand_line(self.items), 'lines')
        return dumps(self.expand_line(self.items))

    def load(self, contents):
        # Going to start adding device profiles post 2.2
        tokens = list(DEFAULT_COMMENT_TOKENS)
        if self._device_os == 'sros':
            tokens.append('echo')
            self._config = parse(contents, indent=4, comment_tokens=tokens)
        else:
            self._config = parse(contents, indent=self.indent)

    def load_from_file(self, filename):
        self.load(open(filename).read())

    def get(self, path):
        if isinstance(path, string_types):
            path = [path]
        for item in self._config:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)

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

    def expand_line(self, objs):
        visited = set()
        expanded = list()
        for o in objs:
            for p in o.parents:
                if p not in visited:
                    visited.add(p)
                    expanded.append(p)
            expanded.append(o)
            visited.add(o)
        return expanded

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def expand_block(self, objects, visited=None):
        items = list()

        if not visited:
            visited = set()

        for o in objects:
            items.append(o)
            visited.add(o)
            for child in o.children:
                items.extend(self.expand_block([child], visited))

        return items

    def diff_line(self, other, path=None):
        diff = list()
        for item in self.items:
            if item not in other:
                diff.append(item)
        return diff

    def diff_strict(self, other, path=None):
        diff = list()
        for index, item in enumerate(self.items):
            try:
                if item != other[index]:
                    diff.append(item)
            except IndexError:
                diff.append(item)
        return diff

    def diff_exact(self, other, path=None):
        diff = list()
        if len(other) != len(self.items):
            diff.extend(self.items)
        else:
            for ours, theirs in zip(self.items, other):
                if ours != theirs:
                    diff.extend(self.items)
                    break
        return diff

    def difference(self, other, path=None, match='line', replace='line'):
        try:
            if path and match != 'line':
                try:
                    other = other.get_section_objects(path)
                except ValueError:
                    other = list()
            else:
                other = other.items
            func = getattr(self, 'diff_%s' % match)
            updates = func(other, path=path)
        except AttributeError:
            raise
            raise TypeError('invalid value for match keyword')

        if self._device_os == 'junos':
            return updates

        if replace == 'block':
            parents = list()
            for u in updates:
                if u.parents is None:
                    if u not in parents:
                        parents.append(u)
                else:
                    for p in u.parents:
                        if p not in parents:
                            parents.append(p)

            return self.expand_block(parents)

        return self.expand_line(updates)

    def replace(self, patterns, repl, parents=None, add_if_missing=False,
                ignore_whitespace=True):

        match = None

        parents = to_list(parents) or list()
        patterns = [re.compile(r, re.I) for r in to_list(patterns)]

        for item in self.items:
            for regexp in patterns:
                text = item.text
                if not ignore_whitespace:
                    text = item.raw
                if regexp.search(text):
                    if item.text != repl:
                        if parents == [p.text for p in item.parents]:
                            match = item
                            break

        if match:
            match.text = repl
            indent = len(match.raw) - len(match.raw.lstrip())
            match.raw = repl.rjust(len(repl) + indent)

        elif add_if_missing:
            self.add(repl, parents=parents)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)
