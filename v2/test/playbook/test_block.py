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
from ansible.playbook.task import Task
from .. compat import unittest

class TestBlock(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_construct_empty_block(self):
        b = Block()

    def test_construct_block_with_role(self):
        pass

    def test_block__load_list_of_tasks(self):
        task = dict(action='test')
        b = Block()
        self.assertEqual(b._load_list_of_tasks([]), [])
        res = b._load_list_of_tasks([task])
        self.assertEqual(len(res), 1)
        assert isinstance(res[0], Task)
        res = b._load_list_of_tasks([task,task,task])
        self.assertEqual(len(res), 3)

    def test_load_block_simple(self):
        ds = dict(
           begin = [],
           rescue = [],
           end = [],
           otherwise = [],
        )
        b = Block.load(ds)
        self.assertEqual(b.begin, [])
        self.assertEqual(b.rescue, [])
        self.assertEqual(b.end, [])
        self.assertEqual(b.otherwise, [])

    def test_load_block_with_tasks(self):
        ds = dict(
           begin = [dict(action='begin')],
           rescue = [dict(action='rescue')],
           end = [dict(action='end')],
           otherwise = [dict(action='otherwise')],
        )
        b = Block.load(ds)
        self.assertEqual(len(b.begin), 1)
        assert isinstance(b.begin[0], Task)
        self.assertEqual(len(b.rescue), 1)
        assert isinstance(b.rescue[0], Task)
        self.assertEqual(len(b.end), 1)
        assert isinstance(b.end[0], Task)
        self.assertEqual(len(b.otherwise), 1)
        assert isinstance(b.otherwise[0], Task)

