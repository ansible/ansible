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

from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.resolver import Resolver

from ansible.parsing.yaml.composer import AnsibleComposer
from ansible.parsing.yaml.constructor import AnsibleConstructor

class AnsibleLoader(Reader, Scanner, Parser, AnsibleComposer, AnsibleConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        AnsibleComposer.__init__(self)
        AnsibleConstructor.__init__(self)
        Resolver.__init__(self)

