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

from v2.playbook.base import PlaybookBase
from v2.utils import list_union

class Role(PlaybookBase):

    # TODO: this will be overhauled to match Task.py at some point

    def __init__(self):
        pass

    def get_name(self):
        return "TEMPORARY"

    def load(self, ds):
        self._ds = ds
        self._tasks = []
        self._handlers = []
        self._blocks = []
        self._dependencies = []
        self._metadata = dict()
        self._defaults = dict()
        self._vars = dict()
        self._params = dict()

    def get_vars(self):
        # returns the merged variables for this role, including
        # recursively merging those of all child roles
        return dict()

    def get_immediate_dependencies(self):
        return self._dependencies

    def get_all_dependencies(self):
        # returns a list built recursively, of all deps from
        # all child dependencies
        all_deps = []
        for dep in self._dependencies:
            list_union(all_deps, dep.get_all_dependencies())
        all_deps = list_union(all_deps, self.dependencies)
        return all_deps

    def get_blocks(self):
        # should return 
        return self.blocks


