# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


from collections import deque
import unittest
from unittest.mock import patch, MagicMock

from ansible.executor.play_iterator import PlayIterator
from ansible.playbook import Playbook
from ansible.playbook.play_context import PlayContext
from ansible.plugins.strategy import StrategyBase
from ansible.plugins.strategy.linear import StrategyModule
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.host import Host
from ansible._internal import _task

from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop


class TestStrategyLinear(unittest.TestCase):

    def test_run_once_registered_host_variables_are_isolated_per_host(self):
        strategy = StrategyBase.__new__(StrategyBase)
        strategy._results_lock = MagicMock()
        strategy._results = deque()
        strategy._pending_results = 1
        strategy._blocked_hosts = {}
        strategy._queued_task_cache = {('host00', 'task-uuid'): dict(task_vars={}, play_context=MagicMock())}
        strategy._hosts_cache = ['host00', 'host01']
        strategy._diff = False
        strategy.debugger_active = False
        strategy._inventory = MagicMock()
        strategy._inventory.get_hosts.return_value = [Host('host00'), Host('host01')]
        strategy._process_rpc_queue = MagicMock()
        strategy._tqm = MagicMock()
        strategy._tqm._unreachable_hosts = {}
        strategy._tqm._failed_hosts = {}
        strategy._tqm._stats = MagicMock()
        strategy._tqm.send_callback = MagicMock()
        strategy._variable_manager = MagicMock()

        task = MagicMock()
        task.run_once = True
        task.loop = None
        task.delegate_to = None
        task.delegate_facts = False
        task._uuid = 'task-uuid'
        task.debugger = 'never'

        utr = _task.UnifiedTaskResult(is_module=False)
        shared_facts = {'nested': {'marker': 'before'}}
        utr.pending_changes.register_host_variables[_task.VariableLayer.EPHEMERAL_FACT] = shared_facts

        strategy._results.append(_task.HostTaskResult(host=Host('host00'), task=task, utr=utr))

        iterator = MagicMock()
        iterator.host_states = {}

        strategy._process_pending_results(iterator)

        first_call, second_call = strategy._variable_manager.set_nonpersistent_facts.call_args_list
        first_facts = first_call.args[1]
        second_facts = second_call.args[1]

        first_facts['nested']['marker'] = 'after'

        self.assertEqual(second_facts['nested']['marker'], 'before')

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_noop(self):
        fake_loader = DictDataLoader({
            "test_play.yml": """
            - hosts: all
              gather_facts: no
              tasks:
                - block:
                   - block:
                     - name: task1
                       debug: msg='task1'
                       failed_when: inventory_hostname == 'host01'

                     - name: task2
                       debug: msg='task2'

                     rescue:
                       - name: rescue1
                         debug: msg='rescue1'

                       - name: rescue2
                         debug: msg='rescue2'
            """,
        })

        mock_var_manager = MagicMock()
        mock_var_manager._fact_cache = dict()
        mock_var_manager.get_vars.return_value = dict()

        p = Playbook.load('test_play.yml', loader=fake_loader, variable_manager=mock_var_manager)

        inventory = MagicMock()
        inventory.hosts = {}
        hosts = []
        for i in range(0, 2):
            host = MagicMock()
            host.name = host.get_name.return_value = 'host%02d' % i
            hosts.append(host)
            inventory.hosts[host.name] = host
        inventory.get_hosts.return_value = hosts
        inventory.filter_hosts.return_value = hosts

        mock_var_manager._fact_cache['host00'] = dict()

        play_context = PlayContext(play=p._entries[0])

        itr = PlayIterator(
            inventory=inventory,
            play=p._entries[0],
            play_context=play_context,
            variable_manager=mock_var_manager,
            all_vars=dict(),
        )

        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=None,
            forks=5,
        )
        tqm._initialize_processes(3)
        strategy = StrategyModule(tqm)
        strategy._hosts_cache = [h.name for h in hosts]
        strategy._hosts_cache_all = [h.name for h in hosts]

        # debug: task1, debug: task1
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        host1_task = hosts_tasks[0][1]
        host2_task = hosts_tasks[1][1]
        self.assertIsNotNone(host1_task)
        self.assertIsNotNone(host2_task)
        self.assertEqual(host1_task.action, 'debug')
        self.assertEqual(host2_task.action, 'debug')
        self.assertEqual(host1_task.name, 'task1')
        self.assertEqual(host2_task.name, 'task1')

        # mark the second host failed
        itr.mark_host_failed(hosts[1])

        # debug: task2, noop
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        self.assertEqual(len(hosts_tasks), 1)
        host, task = hosts_tasks[0]
        self.assertEqual(host.name, 'host00')
        self.assertEqual(task.action, 'debug')
        self.assertEqual(task.name, 'task2')

        # noop, debug: rescue1
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        self.assertEqual(len(hosts_tasks), 1)
        host, task = hosts_tasks[0]
        self.assertEqual(host.name, 'host01')
        self.assertEqual(task.action, 'debug')
        self.assertEqual(task.name, 'rescue1')

        # noop, debug: rescue2
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        self.assertEqual(len(hosts_tasks), 1)
        host, task = hosts_tasks[0]
        self.assertEqual(host.name, 'host01')
        self.assertEqual(task.action, 'debug')
        self.assertEqual(task.name, 'rescue2')

        # end of iteration
        assert not strategy._get_next_task_lockstep(strategy.get_hosts_left(itr), itr)

    def test_noop_64999(self):
        fake_loader = DictDataLoader({
            "test_play.yml": """
            - hosts: all
              gather_facts: no
              tasks:
                - name: block1
                  block:
                    - name: block2
                      block:
                        - name: block3
                          block:
                          - name: task1
                            debug:
                            failed_when: inventory_hostname == 'host01'
                          rescue:
                            - name: rescue1
                              debug:
                                msg: "rescue"
                        - name: after_rescue1
                          debug:
                            msg: "after_rescue1"
            """,
        })

        mock_var_manager = MagicMock()
        mock_var_manager._fact_cache = dict()
        mock_var_manager.get_vars.return_value = dict()

        p = Playbook.load('test_play.yml', loader=fake_loader, variable_manager=mock_var_manager)

        inventory = MagicMock()
        inventory.hosts = {}
        hosts = []
        for i in range(0, 2):
            host = MagicMock()
            host.name = host.get_name.return_value = 'host%02d' % i
            hosts.append(host)
            inventory.hosts[host.name] = host
        inventory.get_hosts.return_value = hosts
        inventory.filter_hosts.return_value = hosts

        mock_var_manager._fact_cache['host00'] = dict()

        play_context = PlayContext(play=p._entries[0])

        itr = PlayIterator(
            inventory=inventory,
            play=p._entries[0],
            play_context=play_context,
            variable_manager=mock_var_manager,
            all_vars=dict(),
        )

        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=mock_var_manager,
            loader=fake_loader,
            passwords=None,
            forks=5,
        )
        tqm._initialize_processes(3)
        strategy = StrategyModule(tqm)
        strategy._hosts_cache = [h.name for h in hosts]
        strategy._hosts_cache_all = [h.name for h in hosts]

        # debug: task1, debug: task1
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        host1_task = hosts_tasks[0][1]
        host2_task = hosts_tasks[1][1]
        self.assertIsNotNone(host1_task)
        self.assertIsNotNone(host2_task)
        self.assertEqual(host1_task.action, 'debug')
        self.assertEqual(host2_task.action, 'debug')
        self.assertEqual(host1_task.name, 'task1')
        self.assertEqual(host2_task.name, 'task1')

        # mark the second host failed
        itr.mark_host_failed(hosts[1])

        # noop, debug: rescue1
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        self.assertEqual(len(hosts_tasks), 1)
        host, task = hosts_tasks[0]
        self.assertEqual(host.name, 'host01')
        self.assertEqual(task.action, 'debug')
        self.assertEqual(task.name, 'rescue1')

        # debug: after_rescue1, debug: after_rescue1
        hosts_left = strategy.get_hosts_left(itr)
        hosts_tasks = strategy._get_next_task_lockstep(hosts_left, itr)
        host1_task = hosts_tasks[0][1]
        host2_task = hosts_tasks[1][1]
        self.assertIsNotNone(host1_task)
        self.assertIsNotNone(host2_task)
        self.assertEqual(host1_task.action, 'debug')
        self.assertEqual(host2_task.action, 'debug')
        self.assertEqual(host1_task.name, 'after_rescue1')
        self.assertEqual(host2_task.name, 'after_rescue1')

        # end of iteration
        assert not strategy._get_next_task_lockstep(strategy.get_hosts_left(itr), itr)
