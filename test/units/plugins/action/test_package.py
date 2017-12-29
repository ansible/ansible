# (c) 2017, Aidan Feldman <aidan.feldman@gmail.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock, Mock
from ansible.plugins.action.package import ActionModule
from ansible.playbook.task import Task


class TestPackageAction(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_args_name_only(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async_val = False
        connection = Mock()

        task.args = {'name': 'at'}
        play_context.check_mode = False

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)

        self.assertDictEqual(self.mock_am.new_module_args(), {'name': 'at'})

    def test_args_use_removed(self):

        play_context = Mock()
        task = MagicMock(Task)
        task.async_val = False
        connection = Mock()

        task.args = {'name': 'at', 'use': 'yum'}
        play_context.check_mode = False

        self.mock_am = ActionModule(task, connection, play_context, loader=None, templar=None, shared_loader_obj=None)

        self.assertDictEqual(self.mock_am.new_module_args(), {'name': 'at'})
