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

from v2.playbook.base import PlaybookBase

class Task(PlaybookBase):
    def __init__(self, block=None, role=None):
        self.ds    = None
        self.block = block
        self.role  = role

    def load(self, ds):
        self.ds = ds
        self.name = ""

    def get_vars(self):
        return dict()

    def get_role(self):
        return self.role

    def get_block(self):
        return self.block

