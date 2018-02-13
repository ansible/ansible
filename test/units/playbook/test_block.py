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

    # TODO: split copy tests to own test class
    # TODO: split object compare/total ordering to own test class
    # TODO: is there a pytest total ordering fixture?
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


class DifferentType():
    pass


class _EqualityCompare():

    def test_eq(self):
        self.assertTrue(self.one == self.one)
        self.assertFalse(self.one == self.two)

    def test_ne(self):
        self.assertFalse(self.one != self.one)
        self.assertTrue(self.one != self.two)

    def test_eq_different(self):
        self.assertFalse(self.one == self.different)
        self.assertTrue(self.one != self.different)


class _TotalOrdering():
    def test_lt(self):
        self.assertFalse(self.one < self.one)
        self.assertTrue(self.one < self.two)
        self.assertFalse(self.two < self.one)

    def test_gt(self):
        self.assertFalse(self.one > self.one)
        self.assertFalse(self.one > self.two)
        self.assertTrue(self.two > self.one)

    def test_le(self):
        self.assertLessEqual(self.one, self.one)
        self.assertTrue(self.one <= self.one)

        self.assertLessEqual(self.one, self.two)
        self.assertTrue(self.one <= self.two)

        self.assertFalse(self.two <= self.one)

    def test_ge(self):
        self.assertGreaterEqual(self.one, self.one)
        self.assertTrue(self.one >= self.one)

        self.assertFalse(self.one >= self.two)

        self.assertGreaterEqual(self.two, self.one)
        self.assertTrue(self.two >= self.one)


class _HashCompare():
    def test_hash_different(self):
        self.assertNotEqual(hash(self.one), hash(self.different))

    def test_hash(self):
        self.assertNotEqual(hash(self.one), hash(self.two))


class _IdentityCompare():
    def test_is(self):
        self.assertFalse(self.one is self.two)
        self.assertFalse(self.one is self.another_one)
        self.assertFalse(self.one is self.different)

    def test_not_is(self):
        self.assertTrue(self.one is not self.two)
        self.assertTrue(self.one is not self.another_one)
        self.assertTrue(self.one is not self.different)


    def test_id(self):
        # the ids should never be the same
        self.assertNotEqual(id(self.one), id(self.two))
        self.assertNotEqual(id(self.two), id(self.different))
        self.assertNotEqual(id(self.one), id(self.different))


class IntTutpleTotalOrdering(unittest.TestCase, _TotalOrdering, _EqualityCompare, _HashCompare):
    def setUp(self):
        self.one = (1,)
        self.two = (2,)
        self.another_one = (1,)
        self.different = DifferentType()


class BlockTotalOrdering(unittest.TestCase,  _EqualityCompare, _HashCompare):
    def setUp(self):
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        raw_block_one = Block()
        fake_loader = DictDataLoader({})
        block_one = raw_block_one.load(block_ds, loader=fake_loader)
        # object with value A
        self.one = block_one

        block_two_ds = {'block': [],
                        'rescue': [],
                        'always': []
                        }
        raw_block_two = Block()
        fake_loader = DictDataLoader({})
        block_two = raw_block_two.load(block_two_ds, loader=fake_loader)
        # same type, different values
        self.two = block_two

        # A different instance of SomeObject but should compare the same as self.one
        block_ds = {'block': [],
                    'rescue': [],
                    'always': []
                    }
        raw_block_another_one = Block()
        fake_loader = DictDataLoader({})
        block_another_one = raw_block_another_one.load(block_ds, loader=fake_loader)
        # object with value A
        self.another_one = block_another_one
        self.another_one = self.one.copy(exclude_parent=True, exclude_tasks=True)

        # A non-None object of a different type than one,two, or another_one
        self.different = DifferentType()
