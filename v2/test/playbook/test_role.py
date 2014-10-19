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

from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from .. compat import unittest

class TestRole(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_construct_empty_block(self):
        r = Role()

    def test_role__load_list_of_blocks(self):
        task = dict(action='test')
        r = Role()
        self.assertEqual(r._load_list_of_blocks([]), [])
        res = r._load_list_of_blocks([task])
        self.assertEqual(len(res), 1)
        assert isinstance(res[0], Block)
        res = r._load_list_of_blocks([task,task,task])
        self.assertEqual(len(res), 3)

    def test_load_role_simple(self):
        pass

    def test_load_role_complex(self):
        pass
