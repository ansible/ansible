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

from abc import ABCMeta, abstractmethod

from ansible.compat.six import with_metaclass

class InventoryParser(with_metaclass(ABCMeta, object)):
    '''Abstract Base Class for retrieving inventory information

    Any InventoryParser functions by taking an inven_source.  The caller then
    calls the parser() method.  Once parser is called, the caller can access
    InventoryParser.hosts for a mapping of Host objects and
    InventoryParser.Groups for a mapping of Group objects.
    '''

    def __init__(self, inven_source):
        '''
        InventoryParser contructors take a source of inventory information
        that they will parse the host and group information from.
        '''
        self.inven_source = inven_source
        self.reset_parser()

    @abstractmethod
    def reset_parser(self):
        '''
        InventoryParsers generally cache their data once parser() is
        called.  This method initializes any parser state before calling parser
        again.
        '''
        self.hosts = dict()
        self.groups = dict()
        self.parsed = False

    def _merge(self, target, addition):
        '''
        This method is provided to InventoryParsers to merge host or group
        dicts since it may take several passes to get all of the data

        Example usage:
            self.hosts = self.from_ini(filename)
            new_hosts = self.from_script(scriptname)
            self._merge(self.hosts, new_hosts)
        '''
        for i in addition:
            if i in target:
                target[i].merge(addition[i])
            else:
                target[i] = addition[i]

    @abstractmethod
    def parse(self, refresh=False):
        if refresh:
            self.reset_parser()
        if self.parsed:
            return self.parsed

        # Parse self.inven_sources here
        pass

