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

from unittest import mock

import unittest
from unittest.mock import patch, MagicMock
from ansible.errors import AnsibleError
from ansible.executor.task_executor import TaskExecutor
from ansible.plugins.loader import action_loader, lookup_loader

from collections import namedtuple
from units.mock.loader import DictDataLoader

get_with_context_result = namedtuple('get_with_context_result', ['object', 'plugin_load_context'])


class TestTaskExecutor(unittest.TestCase):

    def test_task_executor_init(self):
        fake_loader = DictDataLoader({})
        mock_host = MagicMock()
        mock_task = MagicMock()
        mock_play_context = MagicMock()
        mock_shared_loader = MagicMock()
        job_vars = dict()
        mock_queue = MagicMock()
        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
            variable_manager=MagicMock(),
        )

    def test_task_executor_run(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task._role._role_path = '/path/to/role/foo'

        mock_play_context = MagicMock()

        mock_shared_loader = MagicMock()
        mock_queue = MagicMock()

        job_vars = dict()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
            variable_manager=MagicMock(),
        )

        te._get_loop_items = MagicMock(return_value=None)
        te._execute = MagicMock(return_value=dict())
        res = te.run()

        te._get_loop_items = MagicMock(return_value=[])
        res = te.run()

        te._get_loop_items = MagicMock(return_value=['a', 'b', 'c'])
        te._run_loop = MagicMock(return_value=[dict(item='a', changed=True), dict(item='b', failed=True), dict(item='c')])
        res = te.run()

        te._get_loop_items = MagicMock(side_effect=AnsibleError(""))
        res = te.run()
        self.assertIn("failed", res)

    def test_task_executor_get_loop_items(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task.loop_with = 'items'
        mock_task.loop = ['a', 'b', 'c']

        mock_play_context = MagicMock()

        mock_shared_loader = MagicMock()
        mock_shared_loader.lookup_loader = lookup_loader

        job_vars = dict()
        mock_queue = MagicMock()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
            variable_manager=MagicMock(),
        )

        items = te._get_loop_items()
        self.assertEqual(items, ['a', 'b', 'c'])

    def test_task_executor_run_loop(self):
        items = ['a', 'b', 'c']

        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        def _copy(exclude_parent=False, exclude_tasks=False):
            new_item = MagicMock()
            new_item.loop_control = MagicMock(break_when=[])
            return new_item

        mock_task = MagicMock()
        mock_task.loop_control = MagicMock(break_when=[])
        mock_task.copy.side_effect = _copy

        mock_play_context = MagicMock()

        mock_shared_loader = MagicMock()
        mock_queue = MagicMock()

        job_vars = dict()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
            variable_manager=MagicMock(),
        )

        te._task.loop_control.label = "bob"

        def _execute(templar, variables):
            return dict(item=variables.get('item'))

        te._execute = MagicMock(side_effect=_execute)

        res = te._run_loop(items)
        self.assertEqual(len(res), 3)

    def test_task_executor_get_action_handler(self):
        te = TaskExecutor(
            host=MagicMock(),
            task=MagicMock(),
            job_vars={},
            play_context=MagicMock(),
            loader=DictDataLoader({}),
            shared_loader_obj=MagicMock(),
            final_q=MagicMock(),
            variable_manager=MagicMock(),
        )

        context = MagicMock(resolved=False)
        te._shared_loader_obj.module_loader.find_plugin_with_context.return_value = context
        action_loader = te._shared_loader_obj.action_loader
        action_loader.has_plugin.return_value = True
        action_loader.get.return_value = mock.sentinel.handler

        mock_templar = MagicMock()
        action = 'namespace.prefix_suffix'
        te._task.action = action
        te._connection = MagicMock()

        with patch('ansible.executor.task_executor.start_connection'):
            handler = te._get_action_handler(mock_templar)

        self.assertIs(mock.sentinel.handler, handler)

        action_loader.has_plugin.assert_called_once_with(action, collection_list=te._task.collections)

        action_loader.get.assert_called_with(
            te._task.action, task=te._task, connection=te._connection,
            play_context=te._play_context, loader=te._loader,
            templar=unittest.mock.ANY, shared_loader_obj=te._shared_loader_obj,
            collection_list=te._task.collections)

    def test_task_executor_get_handler_prefix(self):
        te = TaskExecutor(
            host=MagicMock(),
            task=MagicMock(),
            job_vars={},
            play_context=MagicMock(),
            loader=DictDataLoader({}),
            shared_loader_obj=MagicMock(),
            final_q=MagicMock(),
            variable_manager=MagicMock(),
        )

        context = MagicMock(resolved=False)
        te._shared_loader_obj.module_loader.find_plugin_with_context.return_value = context
        action_loader = te._shared_loader_obj.action_loader
        action_loader.has_plugin.side_effect = [False, True]
        action_loader.get.return_value = mock.sentinel.handler
        action_loader.__contains__.return_value = True

        mock_templar = MagicMock()
        action = 'namespace.netconf_suffix'
        module_prefix = action.split('_', 1)[0]
        te._task.action = action
        te._connection = MagicMock()

        with patch('ansible.executor.task_executor.start_connection'):
            handler = te._get_action_handler(mock_templar)

        self.assertIs(mock.sentinel.handler, handler)
        action_loader.has_plugin.assert_has_calls([mock.call(action, collection_list=te._task.collections),  # called twice
                                                   mock.call(module_prefix, collection_list=te._task.collections)])

        action_loader.get.assert_called_with(
            module_prefix, task=te._task, connection=te._connection,
            play_context=te._play_context, loader=te._loader,
            templar=unittest.mock.ANY, shared_loader_obj=te._shared_loader_obj,
            collection_list=te._task.collections)

    def test_task_executor_get_handler_normal(self):
        te = TaskExecutor(
            host=MagicMock(),
            task=MagicMock(),
            job_vars={},
            play_context=MagicMock(),
            loader=DictDataLoader({}),
            shared_loader_obj=MagicMock(),
            final_q=MagicMock(),
            variable_manager=MagicMock(),
        )

        action_loader = te._shared_loader_obj.action_loader
        action_loader.has_plugin.return_value = False
        action_loader.get.return_value = mock.sentinel.handler
        action_loader.__contains__.return_value = False
        module_loader = te._shared_loader_obj.module_loader
        context = MagicMock(resolved=False)
        module_loader.find_plugin_with_context.return_value = context

        mock_templar = MagicMock()
        action = 'namespace.prefix_suffix'
        module_prefix = action.split('_', 1)[0]
        te._task.action = action
        te._connection = MagicMock()

        with patch('ansible.executor.task_executor.start_connection'):
            handler = te._get_action_handler(mock_templar)

        self.assertIs(mock.sentinel.handler, handler)

        action_loader.has_plugin.assert_has_calls([mock.call(action, collection_list=te._task.collections)])

        action_loader.get.assert_called_with(
            'ansible.legacy.normal', task=te._task, connection=te._connection,
            play_context=te._play_context, loader=te._loader,
            templar=unittest.mock.ANY, shared_loader_obj=te._shared_loader_obj,
            collection_list=None)

    def test_task_executor_execute(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task.action = 'mock.action'
        mock_task.args = dict()
        mock_task.become = False
        mock_task.retries = 0
        mock_task.delay = -1
        mock_task.delegate_to = None
        mock_task.register = 'foo'
        mock_task.until = None
        mock_task.changed_when = None
        mock_task.failed_when = None
        mock_task.post_validate.return_value = None
        # mock_task.async_val cannot be left unset, because on Python 3 MagicMock()
        # > 0 raises a TypeError   There are two reasons for using the value 1
        # here: on Python 2 comparing MagicMock() > 0 returns True, and the
        # other reason is that if I specify 0 here, the test fails. ;)
        mock_task.async_val = 1
        mock_task.poll = 0
        mock_task.timeout = None
        mock_task.evaluate_conditional_with_result.return_value = (True, None)

        mock_play_context = MagicMock()
        mock_play_context.post_validate.return_value = None
        mock_play_context.update_vars.return_value = None

        mock_connection = MagicMock()
        mock_connection.force_persistence = False
        mock_connection.supports_persistence = False
        mock_connection.set_host_overrides.return_value = None
        mock_connection._connect.return_value = None

        mock_action = MagicMock()
        mock_queue = MagicMock()

        mock_vm = MagicMock()
        mock_vm.get_delegated_vars_and_hostname.return_value = {}, None

        shared_loader = MagicMock()
        shared_loader.action_loader.get.return_value = mock_action
        new_stdin = None
        job_vars = dict(omit="XXXXXXXXXXXXXXXXXXX")

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=shared_loader,
            final_q=mock_queue,
            variable_manager=mock_vm,
        )

        te._get_connection = MagicMock(return_value=mock_connection)
        context = MagicMock()

        with patch('ansible.executor.task_executor.start_connection'):
            te._get_action_handler_with_context = MagicMock(return_value=get_with_context_result(mock_action, context))

        mock_action.run.return_value = dict(ansible_facts=dict())
        res = te._execute(te._task_templar, te._job_vars)

        mock_task.changed_when = MagicMock(return_value="1 == 1")
        res = te._execute(te._task_templar, te._job_vars)

        mock_task.changed_when = None
        mock_task.failed_when = MagicMock(return_value="1 == 1")
        res = te._execute(te._task_templar, te._job_vars)

        mock_task.failed_when = None
        mock_task.evaluate_conditional.return_value = False
        res = te._execute(te._task_templar, te._job_vars)

        mock_task.evaluate_conditional.return_value = True
        mock_task.args = dict(_raw_params='foo.yml', a='foo', b='bar')
        mock_task.action = 'include'
        res = te._execute(te._task_templar, te._job_vars)

    def test_task_executor_poll_async_result(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task.async_val = 0.1
        mock_task.poll = 0.05

        mock_play_context = MagicMock()

        mock_action = MagicMock()
        mock_queue = MagicMock()

        shared_loader = MagicMock()
        shared_loader.action_loader = action_loader

        job_vars = dict(omit="XXXXXXXXXXXXXXXXXXX")

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            loader=fake_loader,
            shared_loader_obj=shared_loader,
            final_q=mock_queue,
            variable_manager=MagicMock(),
        )

        te._connection = MagicMock()

        def _get(*args, **kwargs):
            mock_action = MagicMock()
            mock_action.run.return_value = dict(stdout='')
            return mock_action

        # testing with some bad values in the result passed to poll async,
        # and with a bad value returned from the mock action
        with patch.object(action_loader, 'get', _get):
            mock_templar = MagicMock()
            res = te._poll_async_result(result=dict(), templar=mock_templar)
            self.assertIn('failed', res)
            res = te._poll_async_result(result=dict(ansible_job_id=1), templar=mock_templar)
            self.assertIn('failed', res)

        def _get(*args, **kwargs):
            mock_action = MagicMock()
            mock_action.run.return_value = dict(finished=1)
            return mock_action

        # now testing with good values
        with patch.object(action_loader, 'get', _get):
            mock_templar = MagicMock()
            res = te._poll_async_result(result=dict(ansible_job_id=1), templar=mock_templar)
            self.assertEqual(res, dict(finished=1))
