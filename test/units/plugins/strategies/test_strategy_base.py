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
from ansible.plugins.strategy import StrategyBase
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.task_result import TaskResult
from ansible.playbook.handler import Handler
from ansible.inventory.host import Host

from six.moves import queue as Queue
from units.mock.loader import DictDataLoader

class TestStrategyBase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_strategy_base_init(self):
        mock_tqm = MagicMock(TaskQueueManager)
        mock_tqm._final_q = MagicMock()
        mock_tqm._options = MagicMock()
        strategy_base = StrategyBase(tqm=mock_tqm)

    def test_strategy_base_run(self):
        mock_tqm = MagicMock(TaskQueueManager)
        mock_tqm._final_q = MagicMock()
        mock_tqm._stats = MagicMock()
        mock_tqm.send_callback.return_value = None

        mock_iterator  = MagicMock()
        mock_iterator._play = MagicMock()
        mock_iterator._play.handlers = []

        mock_play_context = MagicMock()

        mock_tqm._failed_hosts = dict()
        mock_tqm._unreachable_hosts = dict()
        mock_tqm._options = MagicMock()
        strategy_base = StrategyBase(tqm=mock_tqm)

        self.assertEqual(strategy_base.run(iterator=mock_iterator, play_context=mock_play_context), 0)
        self.assertEqual(strategy_base.run(iterator=mock_iterator, play_context=mock_play_context, result=False), 1)
        mock_tqm._failed_hosts = dict(host1=True)
        self.assertEqual(strategy_base.run(iterator=mock_iterator, play_context=mock_play_context, result=False), 2)
        mock_tqm._unreachable_hosts = dict(host1=True)
        self.assertEqual(strategy_base.run(iterator=mock_iterator, play_context=mock_play_context, result=False), 3)

    def test_strategy_base_get_hosts(self):
        mock_hosts = []
        for i in range(0, 5):
            mock_host = MagicMock()
            mock_host.name = "host%02d" % (i+1)
            mock_host.has_hostkey = True
            mock_hosts.append(mock_host)

        mock_inventory = MagicMock()
        mock_inventory.get_hosts.return_value = mock_hosts

        mock_tqm = MagicMock()
        mock_tqm._final_q = MagicMock()
        mock_tqm.get_inventory.return_value = mock_inventory

        mock_play = MagicMock()
        mock_play.hosts = ["host%02d" % (i+1) for i in range(0, 5)]

        strategy_base = StrategyBase(tqm=mock_tqm)

        mock_tqm._failed_hosts = []
        mock_tqm._unreachable_hosts = []
        self.assertEqual(strategy_base.get_hosts_remaining(play=mock_play), mock_hosts)
        
        mock_tqm._failed_hosts = ["host01"]
        self.assertEqual(strategy_base.get_hosts_remaining(play=mock_play), mock_hosts[1:])
        self.assertEqual(strategy_base.get_failed_hosts(play=mock_play), [mock_hosts[0]])

        mock_tqm._unreachable_hosts = ["host02"]
        self.assertEqual(strategy_base.get_hosts_remaining(play=mock_play), mock_hosts[2:])

    @patch.object(WorkerProcess, 'run')
    def test_strategy_base_queue_task(self, mock_worker):
        def fake_run(self):
            return

        mock_worker.run.side_effect = fake_run

        fake_loader = DictDataLoader()
        mock_var_manager = MagicMock()
        mock_host = MagicMock()
        mock_host.has_hostkey = True
        mock_inventory = MagicMock()
        mock_options = MagicMock()
        mock_options.module_path = None
        
        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            options=mock_options,
            passwords=None,
        )
        tqm._initialize_processes(3)
        tqm.hostvars = dict()

        try:
            strategy_base = StrategyBase(tqm=tqm)
            strategy_base._queue_task(host=mock_host, task=MagicMock(), task_vars=dict(), play_context=MagicMock())
            self.assertEqual(strategy_base._cur_worker, 1)
            self.assertEqual(strategy_base._pending_results, 1)
            strategy_base._queue_task(host=mock_host, task=MagicMock(), task_vars=dict(), play_context=MagicMock())
            self.assertEqual(strategy_base._cur_worker, 2)
            self.assertEqual(strategy_base._pending_results, 2)
            strategy_base._queue_task(host=mock_host, task=MagicMock(), task_vars=dict(), play_context=MagicMock())
            self.assertEqual(strategy_base._cur_worker, 0)
            self.assertEqual(strategy_base._pending_results, 3)
        finally:
            tqm.cleanup()
        

    def test_strategy_base_process_pending_results(self):
        mock_tqm = MagicMock()
        mock_tqm._terminated = False
        mock_tqm._failed_hosts = dict()
        mock_tqm._unreachable_hosts = dict()
        mock_tqm.send_callback.return_value = None

        queue_items = []
        def _queue_empty(*args, **kwargs):
            return len(queue_items) == 0
        def _queue_get(*args, **kwargs):
            if len(queue_items) == 0:
                raise Queue.Empty
            else:
                return queue_items.pop()
            
        mock_queue = MagicMock()
        mock_queue.empty.side_effect = _queue_empty
        mock_queue.get.side_effect = _queue_get
        mock_tqm._final_q = mock_queue

        mock_tqm._stats = MagicMock()
        mock_tqm._stats.increment.return_value = None
        
        mock_iterator = MagicMock()
        mock_iterator.mark_host_failed.return_value = None
        mock_iterator.get_next_task_for_host.return_value = (None, None)

        mock_host = MagicMock()
        mock_host.name = 'test01'
        mock_host.vars = dict()
        mock_host.has_hostkey = True

        mock_task = MagicMock()
        mock_task._role = None
        mock_task.ignore_errors = False

        mock_group = MagicMock()
        mock_group.add_host.return_value = None

        def _get_host(host_name):
            if host_name == 'test01':
                return mock_host
            return None
        def _get_group(group_name):
            if group_name in ('all', 'foo'):
                return mock_group
            return None

        mock_inventory = MagicMock()
        mock_inventory._hosts_cache = dict()
        mock_inventory.get_host.side_effect = _get_host
        mock_inventory.get_group.side_effect = _get_group
        mock_inventory.clear_pattern_cache.return_value = None
        mock_inventory.get_host_vars.return_value = {}

        mock_var_mgr = MagicMock()
        mock_var_mgr.set_host_variable.return_value = None
        mock_var_mgr.set_host_facts.return_value = None

        strategy_base = StrategyBase(tqm=mock_tqm)
        strategy_base._inventory = mock_inventory
        strategy_base._variable_manager = mock_var_mgr
        strategy_base._blocked_hosts = dict()
        strategy_base._notified_handlers = dict()

        results = strategy_base._wait_on_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)

        task_result = TaskResult(host=mock_host, task=mock_task, return_data=dict(changed=True))
        queue_items.append(('host_task_ok', task_result))
        strategy_base._blocked_hosts['test01'] = True
        strategy_base._pending_results = 1
        results = strategy_base._wait_on_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], task_result)
        self.assertEqual(strategy_base._pending_results, 0)
        self.assertNotIn('test01', strategy_base._blocked_hosts)

        task_result = TaskResult(host=mock_host, task=mock_task, return_data='{"failed":true}')
        queue_items.append(('host_task_failed', task_result))
        strategy_base._blocked_hosts['test01'] = True
        strategy_base._pending_results = 1
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], task_result)
        self.assertEqual(strategy_base._pending_results, 0)
        self.assertNotIn('test01', strategy_base._blocked_hosts)
        self.assertIn('test01', mock_tqm._failed_hosts)
        del mock_tqm._failed_hosts['test01']

        task_result = TaskResult(host=mock_host, task=mock_task, return_data='{}')
        queue_items.append(('host_unreachable', task_result))
        strategy_base._blocked_hosts['test01'] = True
        strategy_base._pending_results = 1
        results = strategy_base._wait_on_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], task_result)
        self.assertEqual(strategy_base._pending_results, 0)
        self.assertNotIn('test01', strategy_base._blocked_hosts)
        self.assertIn('test01', mock_tqm._unreachable_hosts)
        del mock_tqm._unreachable_hosts['test01']

        task_result = TaskResult(host=mock_host, task=mock_task, return_data='{}')
        queue_items.append(('host_task_skipped', task_result))
        strategy_base._blocked_hosts['test01'] = True
        strategy_base._pending_results = 1
        results = strategy_base._wait_on_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], task_result)
        self.assertEqual(strategy_base._pending_results, 0)
        self.assertNotIn('test01', strategy_base._blocked_hosts)

        strategy_base._blocked_hosts['test01'] = True
        strategy_base._pending_results = 1

        queue_items.append(('add_host', dict(add_host=dict(host_name='newhost01', new_groups=['foo']))))
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)
        self.assertEqual(strategy_base._pending_results, 1)
        self.assertIn('test01', strategy_base._blocked_hosts)

        queue_items.append(('add_group', mock_host, dict(add_group=dict(group_name='foo'))))
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)
        self.assertEqual(strategy_base._pending_results, 1)
        self.assertIn('test01', strategy_base._blocked_hosts)

        task_result = TaskResult(host=mock_host, task=mock_task, return_data=dict(changed=True))
        queue_items.append(('notify_handler', task_result, 'test handler'))
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)
        self.assertEqual(strategy_base._pending_results, 1)
        self.assertIn('test01', strategy_base._blocked_hosts)
        self.assertIn('test handler', strategy_base._notified_handlers)
        self.assertIn(mock_host, strategy_base._notified_handlers['test handler'])

        queue_items.append(('set_host_var', mock_host, mock_task, None, 'foo', 'bar'))
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)
        self.assertEqual(strategy_base._pending_results, 1)

        queue_items.append(('set_host_facts', mock_host, mock_task, None, 'foo', dict()))
        results = strategy_base._process_pending_results(iterator=mock_iterator)
        self.assertEqual(len(results), 0)
        self.assertEqual(strategy_base._pending_results, 1)

        queue_items.append(('bad'))
        self.assertRaises(AnsibleError, strategy_base._process_pending_results, iterator=mock_iterator)

    def test_strategy_base_load_included_file(self):
        fake_loader = DictDataLoader({
            "test.yml": """
            - debug: msg='foo'
            """,
            "bad.yml": """
            """,
        })

        mock_tqm = MagicMock()
        mock_tqm._final_q = MagicMock()

        strategy_base = StrategyBase(tqm=mock_tqm)
        strategy_base._loader = fake_loader

        mock_play = MagicMock()

        mock_block = MagicMock()
        mock_block._play = mock_play
        mock_block.vars = dict()

        mock_task = MagicMock()
        mock_task._block = mock_block
        mock_task._role = None

        mock_iterator = MagicMock()
        mock_iterator.mark_host_failed.return_value = None

        mock_inc_file = MagicMock()
        mock_inc_file._task = mock_task

        mock_inc_file._filename = "test.yml"
        res = strategy_base._load_included_file(included_file=mock_inc_file, iterator=mock_iterator)

        mock_inc_file._filename = "bad.yml"
        res = strategy_base._load_included_file(included_file=mock_inc_file, iterator=mock_iterator)
        self.assertEqual(res, [])

    @patch.object(WorkerProcess, 'run')
    def test_strategy_base_run_handlers(self, mock_worker):
        def fake_run(*args):
            return
        mock_worker.side_effect = fake_run
        mock_play_context = MagicMock()

        mock_handler_task = MagicMock(Handler)
        mock_handler_task.action = 'foo'
        mock_handler_task.get_name.return_value = "test handler"
        mock_handler_task.has_triggered.return_value = False

        mock_handler = MagicMock()
        mock_handler.block = [mock_handler_task]
        mock_handler.flag_for_host.return_value = False

        mock_play = MagicMock()
        mock_play.handlers = [mock_handler]

        mock_host = MagicMock(Host)
        mock_host.name = "test01"
        mock_host.has_hostkey = True

        mock_inventory = MagicMock()
        mock_inventory.get_hosts.return_value = [mock_host]

        mock_var_mgr = MagicMock()
        mock_var_mgr.get_vars.return_value = dict()

        mock_iterator = MagicMock
        mock_iterator._play = mock_play

        fake_loader = DictDataLoader()
        mock_options = MagicMock()
        mock_options.module_path = None

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_mgr,
            loader=fake_loader,
            options=mock_options,
            passwords=None,
        )
        tqm._initialize_processes(3)
        tqm.hostvars = dict()

        try:
            strategy_base = StrategyBase(tqm=tqm)

            strategy_base._inventory = mock_inventory
            strategy_base._notified_handlers = {"test handler": [mock_host]}

            task_result = TaskResult(Host('host01'), Handler(), dict(changed=False))
            tqm._final_q.put(('host_task_ok', task_result))

            result = strategy_base.run_handlers(iterator=mock_iterator, play_context=mock_play_context)
        finally:
            tqm.cleanup()
