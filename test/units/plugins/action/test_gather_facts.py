# (c) 2016, Saran Ahluwalia <ahlusar.ahluwalia@gmail.com>
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

from units.compat import unittest
from units.compat.mock import MagicMock, patch

from ansible import constants as C
from ansible.playbook.task import Task
from ansible.plugins.action.gather_facts import ActionModule as GatherFactsAction
from ansible.template import Templar
from ansible.executor import module_common

from units.mock.loader import DictDataLoader


class TestNetworkFacts(unittest.TestCase):
    task = MagicMock(Task)
    play_context = MagicMock()
    play_context.check_mode = False
    connection = MagicMock()
    fake_loader = DictDataLoader({
    })
    templar = Templar(loader=fake_loader)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch.object(module_common, '_get_collection_metadata', return_value={})
    def test_network_gather_facts_smart_facts_module(self, mock_collection_metadata):
        self.fqcn_task_vars = {'ansible_network_os': 'ios'}
        self.task.action = 'gather_facts'
        self.task.async_val = False
        self.task.args = {}

        plugin = GatherFactsAction(self.task, self.connection, self.play_context, loader=None, templar=self.templar, shared_loader_obj=None)
        get_module_args = MagicMock()
        plugin._get_module_args = get_module_args
        plugin._execute_module = MagicMock()

        res = plugin.run(task_vars=self.fqcn_task_vars)

        # assert the gather_facts config is 'smart'
        facts_modules = C.config.get_config_value('FACTS_MODULES', variables=self.fqcn_task_vars)
        self.assertEqual(facts_modules, ['smart'])

        # assert the correct module was found
        self.assertEqual(get_module_args.call_count, 1)

        self.assertEqual(
            get_module_args.call_args.args,
            ('ansible.legacy.ios_facts', {'ansible_network_os': 'ios'},)
        )

    @patch.object(module_common, '_get_collection_metadata', return_value={})
    def test_network_gather_facts_smart_facts_module_fqcn(self, mock_collection_metadata):
        self.fqcn_task_vars = {'ansible_network_os': 'cisco.ios.ios'}
        self.task.action = 'gather_facts'
        self.task.async_val = False
        self.task.args = {}

        plugin = GatherFactsAction(self.task, self.connection, self.play_context, loader=None, templar=self.templar, shared_loader_obj=None)
        get_module_args = MagicMock()
        plugin._get_module_args = get_module_args
        plugin._execute_module = MagicMock()

        res = plugin.run(task_vars=self.fqcn_task_vars)

        # assert the gather_facts config is 'smart'
        facts_modules = C.config.get_config_value('FACTS_MODULES', variables=self.fqcn_task_vars)
        self.assertEqual(facts_modules, ['smart'])

        # assert the correct module was found
        self.assertEqual(get_module_args.call_count, 1)

        self.assertEqual(
            get_module_args.call_args.args,
            ('cisco.ios.ios_facts', {'ansible_network_os': 'cisco.ios.ios'},)
        )
