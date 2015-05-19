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

from ansible.plugins.strategies import StrategyBase
from ansible.executor.task_queue_manager import TaskQueueManager

from units.mock.loader import DictDataLoader

class TestVariableManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_strategy_base_init(self):
        mock_tqm = MagicMock(TaskQueueManager)
        mock_tqm._final_q = MagicMock()
        strategy_base = StrategyBase(tqm=mock_tqm)

    def test_strategy_base_run(self):
        mock_tqm = MagicMock(TaskQueueManager)
        mock_tqm._final_q = MagicMock()
        mock_tqm._stats = MagicMock()
        mock_tqm.send_callback.return_value = None

        mock_iterator  = MagicMock()
        mock_iterator._play = MagicMock()
        mock_iterator._play.handlers = []

        mock_conn_info = MagicMock()

        mock_tqm._failed_hosts = []
        mock_tqm._unreachable_hosts = []
        strategy_base = StrategyBase(tqm=mock_tqm)

	self.assertEqual(strategy_base.run(iterator=mock_iterator, connection_info=mock_conn_info), 0)
        self.assertEqual(strategy_base.run(iterator=mock_iterator, connection_info=mock_conn_info, result=False), 1)
        mock_tqm._failed_hosts = ["host1"]
        self.assertEqual(strategy_base.run(iterator=mock_iterator, connection_info=mock_conn_info, result=False), 2)
        mock_tqm._unreachable_hosts = ["host1"]
        self.assertEqual(strategy_base.run(iterator=mock_iterator, connection_info=mock_conn_info, result=False), 3)

    def test_strategy_base_get_hosts(self):
        mock_hosts = []
        for i in range(0, 5):
            mock_host = MagicMock()
            mock_host.name = "host%02d" % (i+1)
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

    def test_strategy_base_queue_task(self):
        fake_loader = DictDataLoader()

        workers = []
        for i in range(0, 3):
            worker_main_q = MagicMock()
            worker_main_q.put.return_value = None
            worker_result_q = MagicMock()
            workers.append([i, worker_main_q, worker_result_q])

        mock_tqm = MagicMock()
        mock_tqm._final_q = MagicMock()
        mock_tqm.get_workers.return_value = workers
        mock_tqm.get_loader.return_value = fake_loader

        strategy_base = StrategyBase(tqm=mock_tqm)
        strategy_base._cur_worker = 0
        strategy_base._pending_results = 0
        strategy_base._queue_task(host=MagicMock(), task=MagicMock(), task_vars=dict(), connection_info=MagicMock())
        self.assertEqual(strategy_base._cur_worker, 1)
        self.assertEqual(strategy_base._pending_results, 1)
        strategy_base._queue_task(host=MagicMock(), task=MagicMock(), task_vars=dict(), connection_info=MagicMock())
        self.assertEqual(strategy_base._cur_worker, 2)
        self.assertEqual(strategy_base._pending_results, 2)
        strategy_base._queue_task(host=MagicMock(), task=MagicMock(), task_vars=dict(), connection_info=MagicMock())
        self.assertEqual(strategy_base._cur_worker, 0)
        self.assertEqual(strategy_base._pending_results, 3)
        workers[0][1].put.side_effect = EOFError
        strategy_base._queue_task(host=MagicMock(), task=MagicMock(), task_vars=dict(), connection_info=MagicMock())
        self.assertEqual(strategy_base._cur_worker, 1)
        self.assertEqual(strategy_base._pending_results, 3)

