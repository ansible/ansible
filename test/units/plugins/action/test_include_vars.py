# (c) 2016, Allen Sanabria <asanabria@linuxdynasty.org>
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

import os
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock

from ansible.playbook.play_context import PlayContext
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.action.include_vars import ActionModule


class TestIncludeVarsPlugin(unittest.TestCase):

    def test_include_file(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_file = os.path.join(base_path, "fixtures/vars/all/all.yml")
        mock_task.args = dict(file=vars_file)
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['ansible_facts']['testing'], 123)

    def test_return_name_fact(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = os.path.join(base_path, "fixtures/vars")
        mock_task.args = dict(dir=vars_dir, name='foobar')
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertTrue('foobar' in results['ansible_facts'])
        self.assertEqual(results['ansible_facts']['foobar']['testing'], 456)

    def test_correct_load_order(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = os.path.join(base_path, "fixtures/vars")
        mock_task.args = dict(dir=vars_dir)
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['ansible_facts']['testing'], 456)

    def test_matching(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = os.path.join(base_path, "fixtures/vars")
        mock_task.args = dict(dir=vars_dir, files_matching='webapp.yml')
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['ansible_facts']['webapp_containers'], 10)
        self.assertEqual(results['ansible_facts']['base_dir'], 'services')
        self.assertEqual(results['ansible_facts']['testing'], 456)

    def test_ignore_files(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = os.path.join(base_path, "fixtures/vars")
        mock_task.args = dict(dir=vars_dir, ignore_files='webapp.yml')
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(
            results['ansible_facts']['base_dir'], 'environments/development'
        )
        self.assertEqual(results['ansible_facts']['testing'], 789)

    def test_depth(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = (
            os.path.join(base_path, "fixtures/vars/environments/development")
        )
        mock_task.args = dict(dir=vars_dir, depth=1)
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['ansible_facts']['testing'], 789)
        self.assertEqual(
            results['ansible_facts']['base_dir'], 'environments/development'
        )

    def test_fail_dir_does_not_exist(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_dir = os.path.join(base_path, "vars")
        mock_task.args = dict(dir=vars_dir)
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['failed'], True)

    def test_fail_invalid_extension(self):
        mock_task = MagicMock()
        mock_task.action = "include_vars"
        base_path = (
            os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
        )
        vars_file = os.path.join(base_path, "vars/all.py")
        mock_task.args = dict(dir=vars_file)
        mock_connection = MagicMock()
        play_context = PlayContext()
        mock_task.async = None
        loader = DataLoader()
        action_base = (
            ActionModule(
                mock_task, mock_connection, play_context, loader, None, None
            )
        )
        action_base._task._role = None
        results = action_base.run()
        self.assertEqual(results['failed'], True)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
