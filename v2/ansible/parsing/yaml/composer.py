# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from yaml.composer import Composer
from yaml.nodes import MappingNode, ScalarNode

class AnsibleComposer(Composer):
    def __init__(self):
        super(Composer, self).__init__()

    def compose_node(self, parent, index):
        # the line number where the previous token has ended (plus empty lines)
        node = Composer.compose_node(self, parent, index)
        if isinstance(node, (ScalarNode, MappingNode)):
            node.__datasource__ = self.name
            node.__line__ = self.line
            node.__column__ = node.start_mark.column + 1
            node.__line__ = node.start_mark.line + 1

        return node
