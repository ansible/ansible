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

def parse(lines, indent):
        toplevel = re.compile(r'\S')
        childline = re.compile(r'^\s*(.+)$')
        repl = r'([{|}|;])'

        ancestors = list()
        config = list()

        for line in str(lines).split('\n'):
            text = str(re.sub(repl, '', line)).strip()

            cfg = ConfigLine(text)
            cfg.raw = line

            if not text or text[0] in ['!', '#']:
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


