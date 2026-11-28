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

from __future__ import annotations

import pytest
import unittest

from ansible.playbook.block import Block
from ansible.playbook.task import Task


@pytest.mark.usefixtures('collection_loader')
class TestBlock(unittest.TestCase):

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

    def test_filter_tagged_tasks_keeps_role_complete_on_skip_always(self):
        from ansible.playbook.play import Play

        play = Play.load(dict(name='test', hosts='all', gather_facts=False))
        play.skip_tags = ['always']

        b = Block(play=play)
        regular = Task(block=b)
        regular.action = 'debug'
        regular.tags = ['always']

        eor = Task(block=b)
        eor.action = 'meta'
        eor.args = {'_raw_params': 'role_complete'}
        eor.implicit = True
        eor.tags = ['always']

        b.block = [regular, eor]
        filtered = b.filter_tagged_tasks(all_vars={})
        self.assertEqual(filtered.block, [eor])
