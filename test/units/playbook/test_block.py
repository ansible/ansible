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

from units.mock.loader import DictDataLoader
from ansible.compat.tests import unittest

from ansible.playbook.block import Block
from ansible.playbook.task import Task


class TestBlock(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_construct_empty_block(self):
        b = Block()

    def test_construct_block_with_role(self):
        pass

    def test_load_block_simple(self):
        ds = dict(
            block=[],
            rescue=[],
            always=[],
            # otherwise=[],
        )
        b = Block.load(ds)
        self.assertEqual(b.block, [])
        self.assertEqual(b.rescue, [])
        self.assertEqual(b.always, [])
        # not currently used
        # self.assertEqual(b.otherwise, [])

    def test_copy(self):
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        block = Block()
        fake_loader = DictDataLoader({})
        loaded_block = block.load(block_ds, loader=fake_loader)

        block_copy = loaded_block.copy()
        self.assertEqual(loaded_block, block_copy)

    def test_copy_exclude_parent(self):
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        block = Block()
        fake_loader = DictDataLoader({})
        loaded_block = block.load(block_ds, loader=fake_loader)

        block_copy = loaded_block.copy(exclude_parent=True)
        self.assertEqual(loaded_block, block_copy)

    def test_copy_exclude_parent_exclude_tasks(self):
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        block = Block()
        fake_loader = DictDataLoader({})
        loaded_block = block.load(block_ds, loader=fake_loader)

        block_copy = loaded_block.copy(exclude_parent=True, exclude_tasks=True)
        self.assertEqual(loaded_block, block_copy)

    def test_copy_parent(self):
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        block = Block()
        fake_loader = DictDataLoader({})
        loaded_block = block.load(block_ds, loader=fake_loader)

        child_block_ds = {'block': [],
                          'rescue': [],
                          'always': []
                          }
        child_block = Block()
        loaded_child_block = child_block.load(child_block_ds, loader=fake_loader)
        block_copy = loaded_child_block.copy()
        self.assertEqual(loaded_child_block, block_copy)

    def test_load_block_with_tasks(self):
        ds = dict(
            block=[dict(action='block')],
            rescue=[dict(action='rescue')],
            always=[dict(action='always')],
            # otherwise=[dict(action='otherwise')],
        )
        b = Block.load(ds)
        self.assertEqual(len(b.block), 1)
        self.assertIsInstance(b.block[0], Task)
        self.assertEqual(len(b.rescue), 1)
        self.assertIsInstance(b.rescue[0], Task)
        self.assertEqual(len(b.always), 1)
        self.assertIsInstance(b.always[0], Task)
        # not currently used
        # self.assertEqual(len(b.otherwise), 1)
        # self.assertIsInstance(b.otherwise[0], Task)

    def test_load_implicit_block(self):
        ds = [dict(action='foo')]
        b = Block.load(ds)
        self.assertEqual(len(b.block), 1)
        self.assertIsInstance(b.block[0], Task)

    def test_deserialize(self):
        ds = dict(
            block=[dict(action='block')],
            rescue=[dict(action='rescue')],
            always=[dict(action='always')],
        )
        b = Block.load(ds)
        data = dict(parent=ds, parent_type='Block')
        b.deserialize(data)
        self.assertIsInstance(b._parent, Block)
