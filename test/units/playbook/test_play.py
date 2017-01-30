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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.block import Block
from ansible.playbook.play import Play
from ansible.playbook.role import Role

from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop


class TestPlay(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_play(self):
        p = Play.load(dict())
        self.assertEqual(str(p), '')

    def test_basic_play(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            connection='local',
            remote_user="root",
            become=True,
            become_user="testing",
        ))

    def test_play_with_user_conflict(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            user="testing",
            gather_facts=False,
        ))
        self.assertEqual(p.remote_user, "testing")

    def test_play_with_user_conflict(self):
        play_data = dict(
            name="test play",
            hosts=['foo'],
            user="testing",
            remote_user="testing",
        )
        self.assertRaises(AnsibleParserError, Play.load, play_data)

    def test_play_with_tasks(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[dict(action='shell echo "hello world"')],
        ))

    def test_play_with_handlers(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            handlers=[dict(action='shell echo "hello world"')],
        ))

    def test_play_with_pre_tasks(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            pre_tasks=[dict(action='shell echo "hello world"')],
        ))

    def test_play_with_post_tasks(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            post_tasks=[dict(action='shell echo "hello world"')],
        ))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_play_with_roles(self):
        fake_loader = DictDataLoader({
            '/etc/ansible/roles/foo/tasks.yml': """
            - name: role task
              shell: echo "hello world"
            """,
        })

        mock_var_manager = MagicMock()
        mock_var_manager.get_vars.return_value = dict()

        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            roles=['foo'],
        ), loader=fake_loader, variable_manager=mock_var_manager)

        blocks = p.compile()

    def test_play_compile(self):
        p = Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            tasks=[dict(action='shell echo "hello world"')],
        ))

        blocks = p.compile()

        # with a single block, there will still be three
        # implicit meta flush_handler blocks inserted
        self.assertEqual(len(blocks), 4)
