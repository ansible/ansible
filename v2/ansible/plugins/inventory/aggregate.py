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

#############################################

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import InventoryParser
#from . ini import InventoryIniParser
#from . script import InventoryScriptParser

class InventoryAggregateParser(InventoryParser):

    def __init__(self, inven_sources):
        self.inven_source = inven_sources
        self.hosts = dict()
        self.groups = dict()

    def reset_parser(self):
        super(InventoryAggregateParser, self).reset_parser()

    def parse(self, refresh=False):
        # InventoryDirectoryParser is a InventoryAggregateParser so we avoid
        # a circular import by importing here
        from . directory import InventoryAggregateParser
        if super(InventoryAggregateParser, self).parse(refresh):
            return self.parsed

        for entry in self.inven_sources:
            if os.path.sep in entry:
                # file or directory
                if os.path.isdir(entry):
                    parser = directory.InventoryDirectoryParser(filename=entry)
                elif utils.is_executable(entry):
                    parser = InventoryScriptParser(filename=entry)
                else:
                    parser = InventoryIniParser(filename=entry)
            else:
                # hostname
                parser = HostnameParser(hostname=entry)
            hosts, groups = parser.parse()
            self._merge(self.hosts, hosts)
            self._merge(self.groups, groups)
