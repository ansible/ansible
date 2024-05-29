# (c) 2016, Adrian Likins <alikins@redhat.com>
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

import os

import unittest
from unittest.mock import MagicMock
from units.mock.loader import DictDataLoader

from ansible import errors
from ansible.playbook import helpers
from ansible.playbook.block import Block
from ansible.playbook.handler import Handler
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role.include import RoleInclude
from ansible.plugins.loader import init_plugin_loader


init_plugin_loader()


class MixinForMocks(object):
    def _setup(self):
        # This is not a very good mixin, lots of side effects
        self.fake_loader = DictDataLoader({'include_test.yml': "",
                                           'other_include_test.yml': ""})
        self.mock_tqm = MagicMock(name='MockTaskQueueManager')

        self.mock_play = MagicMock(name='MockPlay')
        self.mock_play._attributes = []
        self.mock_play._collections = None

        self.mock_iterator = MagicMock(name='MockIterator')
        self.mock_iterator._play = self.mock_play

        self.mock_inventory = MagicMock(name='MockInventory')
        self.mock_inventory._hosts_cache = dict()

        # TODO: can we use a real VariableManager?
        self.mock_variable_manager = MagicMock(name='MockVariableManager')
        self.mock_variable_manager.get_vars.return_value = dict()

        self.mock_block = MagicMock(name='MockBlock')

        # On macOS /etc is actually /private/etc, tests fail when performing literal /etc checks
        self.fake_role_loader = DictDataLoader({os.path.join(os.path.realpath("/etc"), "ansible/roles/bogus_role/tasks/main.yml"): """
                                                - shell: echo 'hello world'
                                                """})

        self._test_data_path = os.path.dirname(__file__)
        self.fake_include_loader = DictDataLoader({"/dev/null/includes/test_include.yml": """
                                                   - include_tasks: other_test_include.yml
                                                   - shell: echo 'hello world'
                                                   """,
                                                   "/dev/null/includes/static_test_include.yml": """
                                                   - include_tasks: other_test_include.yml
                                                   - shell: echo 'hello static world'
                                                   """,
                                                   "/dev/null/includes/other_test_include.yml": """
                                                   - debug:
                                                       msg: other_test_include_debug
                                                   """})


class TestLoadListOfTasks(unittest.TestCase, MixinForMocks):
    def setUp(self):
        self._setup()

    def _assert_is_task_list_or_blocks(self, results):
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, (Task, Block))

    def test_ds_not_list(self):
        ds = {}
        self.assertRaises(AssertionError, helpers.load_list_of_tasks,
                          ds, self.mock_play, block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None)

    def test_ds_not_dict(self):
        ds = [[]]
        self.assertRaises(AssertionError, helpers.load_list_of_tasks,
                          ds, self.mock_play, block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None)

    def test_empty_task(self):
        ds = [{}]
        self.assertRaisesRegex(errors.AnsibleParserError,
                               "no module/action detected in task",
                               helpers.load_list_of_tasks,
                               ds, play=self.mock_play,
                               variable_manager=self.mock_variable_manager, loader=self.fake_loader)

    def test_empty_task_use_handlers(self):
        ds = [{}]
        self.assertRaisesRegex(errors.AnsibleParserError,
                               "no module/action detected in task.",
                               helpers.load_list_of_tasks,
                               ds,
                               use_handlers=True,
                               play=self.mock_play,
                               variable_manager=self.mock_variable_manager,
                               loader=self.fake_loader)

    def test_one_bogus_block(self):
        ds = [{'block': None}]
        self.assertRaisesRegex(errors.AnsibleParserError,
                               "A malformed block was encountered",
                               helpers.load_list_of_tasks,
                               ds, play=self.mock_play,
                               variable_manager=self.mock_variable_manager, loader=self.fake_loader)

    def test_unknown_action(self):
        action_name = 'foo_test_unknown_action'
        ds = [{'action': action_name}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertEqual(res[0].action, action_name)

    def test_block_unknown_action(self):
        action_name = 'foo_test_block_unknown_action'
        ds = [{
            'block': [{'action': action_name}]
        }]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], Block)
        self._assert_default_block(res[0])

    def _assert_default_block(self, block):
        # the expected defaults
        self.assertIsInstance(block.block, list)
        self.assertEqual(len(block.block), 1)
        self.assertIsInstance(block.rescue, list)
        self.assertEqual(len(block.rescue), 0)
        self.assertIsInstance(block.always, list)
        self.assertEqual(len(block.always), 0)

    def test_block_use_handlers(self):
        ds = [{'block': True}]
        self.assertRaisesRegex(errors.AnsibleParserError,
                               "Using a block as a handler is not supported.",
                               helpers.load_list_of_tasks,
                               ds, play=self.mock_play, use_handlers=True,
                               variable_manager=self.mock_variable_manager, loader=self.fake_loader)

    def test_one_bogus_include_tasks(self):
        ds = [{'include_tasks': 'somefile.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_loader)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], TaskInclude)

    def test_one_bogus_include_tasks_use_handlers(self):
        ds = [{'include_tasks': 'somefile.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play, use_handlers=True,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_loader)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], TaskInclude)

    def test_one_bogus_import_tasks(self):
        ds = [{'import_tasks': 'somefile.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_loader)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 0)

    def test_one_include_tasks(self):
        ds = [{'include_tasks': '/dev/null/includes/other_test_include.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self.assertEqual(len(res), 1)
        self._assert_is_task_list_or_blocks(res)

    def test_one_parent_include_tasks(self):
        ds = [{'include_tasks': '/dev/null/includes/test_include.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], TaskInclude)
        self.assertIsNone(res[0]._parent)

    def test_one_include_tasks_tags(self):
        ds = [{'include_tasks': '/dev/null/includes/other_test_include.yml',
               'tags': ['test_one_include_tags_tag1', 'and_another_tagB']
               }]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], TaskInclude)
        self.assertIn('test_one_include_tags_tag1', res[0].tags)
        self.assertIn('and_another_tagB', res[0].tags)

    def test_one_parent_include_tasks_tags(self):
        ds = [{'include_tasks': '/dev/null/includes/test_include.yml',
               # 'vars': {'tags': ['test_one_parent_include_tags_tag1', 'and_another_tag2']}
               'tags': ['test_one_parent_include_tags_tag1', 'and_another_tag2']
               }
              ]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], TaskInclude)
        self.assertIn('test_one_parent_include_tags_tag1', res[0].tags)
        self.assertIn('and_another_tag2', res[0].tags)

    def test_one_include_tasks_use_handlers(self):
        ds = [{'include_tasks': '/dev/null/includes/other_test_include.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         use_handlers=True,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], Handler)

    def test_one_parent_include_tasks_use_handlers(self):
        ds = [{'include_tasks': '/dev/null/includes/test_include.yml'}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         use_handlers=True,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], Handler)

        # default for Handler
        self.assertEqual(res[0].listen, [])

    # TODO/FIXME: this doesn't seen right
    #  figure out how to get the non-static errors to be raised, this seems to just ignore everything
    def test_one_include_not_static(self):
        ds = [{
            'include_tasks': '/dev/null/includes/static_test_include.yml',
        }]
        # a_block = Block()
        ti_ds = {'include_tasks': '/dev/null/includes/ssdftatic_test_include.yml'}
        a_task_include = TaskInclude()
        ti = a_task_include.load(ti_ds)
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         block=ti,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
        self._assert_is_task_list_or_blocks(res)
        self.assertIsInstance(res[0], Task)
        self.assertEqual(res[0].args['_raw_params'], '/dev/null/includes/static_test_include.yml')

    # TODO/FIXME: This two get stuck trying to make a mock_block into a TaskInclude
#    def test_one_include(self):
#        ds = [{'include': 'other_test_include.yml'}]
#        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
#                                         block=self.mock_block,
#                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
#        print(res)

#    def test_one_parent_include(self):
#        ds = [{'include': 'test_include.yml'}]
#        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
#                                         block=self.mock_block,
#                                         variable_manager=self.mock_variable_manager, loader=self.fake_include_loader)
#        print(res)

    def test_one_bogus_include_role(self):
        ds = [{'include_role': {'name': 'bogus_role'}, 'collections': []}]
        res = helpers.load_list_of_tasks(ds, play=self.mock_play,
                                         block=self.mock_block,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_role_loader)
        self.assertEqual(len(res), 1)
        self._assert_is_task_list_or_blocks(res)

    def test_one_bogus_include_role_use_handlers(self):
        ds = [{'include_role': {'name': 'bogus_role'}, 'collections': []}]

        self.assertRaises(errors.AnsibleError, helpers.load_list_of_tasks,
                          ds,
                          self.mock_play,
                          True,  # use_handlers
                          self.mock_block,
                          self.mock_variable_manager,
                          self.fake_role_loader)


class TestLoadListOfRoles(unittest.TestCase, MixinForMocks):
    def setUp(self):
        self._setup()

    def test_ds_not_list(self):
        ds = {}
        self.assertRaises(AssertionError, helpers.load_list_of_roles,
                          ds, self.mock_play)

    def test_empty_role(self):
        ds = [{}]
        self.assertRaisesRegex(errors.AnsibleError,
                               "role definitions must contain a role name",
                               helpers.load_list_of_roles,
                               ds, self.mock_play,
                               variable_manager=self.mock_variable_manager, loader=self.fake_role_loader)

    def test_empty_role_just_name(self):
        ds = [{'name': 'bogus_role'}]
        res = helpers.load_list_of_roles(ds, self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_role_loader)
        self.assertIsInstance(res, list)
        for r in res:
            self.assertIsInstance(r, RoleInclude)

    def test_block_unknown_action(self):
        ds = [{
            'block': [{'action': 'foo_test_block_unknown_action'}]
        }]
        ds = [{'name': 'bogus_role'}]
        res = helpers.load_list_of_roles(ds, self.mock_play,
                                         variable_manager=self.mock_variable_manager, loader=self.fake_role_loader)
        self.assertIsInstance(res, list)
        for r in res:
            self.assertIsInstance(r, RoleInclude)


class TestLoadListOfBlocks(unittest.TestCase, MixinForMocks):
    def setUp(self):
        self._setup()

    def test_ds_not_list(self):
        ds = {}
        mock_play = MagicMock(name='MockPlay')
        self.assertRaises(AssertionError, helpers.load_list_of_blocks,
                          ds, mock_play, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None)

    def test_empty_block(self):
        ds = [{}]
        mock_play = MagicMock(name='MockPlay')
        self.assertRaisesRegex(errors.AnsibleParserError,
                               "no module/action detected in task",
                               helpers.load_list_of_blocks,
                               ds, mock_play,
                               parent_block=None,
                               role=None,
                               task_include=None,
                               use_handlers=False,
                               variable_manager=None,
                               loader=None)

    def test_block_unknown_action(self):
        ds = [{'action': 'foo', 'collections': []}]
        mock_play = MagicMock(name='MockPlay')
        res = helpers.load_list_of_blocks(ds, mock_play, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None,
                                          loader=None)

        self.assertIsInstance(res, list)
        for block in res:
            self.assertIsInstance(block, Block)
