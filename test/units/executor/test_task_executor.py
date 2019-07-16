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

from units.compat import unittest
from units.compat.mock import patch, MagicMock
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.task_executor import TaskExecutor, remove_omit
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import action_loader, lookup_loader
from ansible.parsing.yaml.objects import AnsibleUnicode

from units.mock.loader import DictDataLoader


class TestTaskExecutor(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_task_executor_init(self):
        fake_loader = DictDataLoader({})
        mock_host = MagicMock()
        mock_task = MagicMock()
        mock_play_context = MagicMock()
        mock_shared_loader = MagicMock()
        new_stdin = None
        job_vars = dict()
        mock_queue = MagicMock()
        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
        )

    def test_task_executor_run(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task._role._role_path = '/path/to/role/foo'

        mock_play_context = MagicMock()

        mock_shared_loader = MagicMock()
        mock_queue = MagicMock()

        new_stdin = None
        job_vars = dict()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
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

        new_stdin = None
        job_vars = dict()
        mock_queue = MagicMock()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
        )

        items = te._get_loop_items()
        self.assertEqual(items, ['a', 'b', 'c'])

    def test_task_executor_run_loop(self):
        items = ['a', 'b', 'c']

        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        def _copy(exclude_parent=False, exclude_tasks=False):
            new_item = MagicMock()
            return new_item

        mock_task = MagicMock()
        mock_task.copy.side_effect = _copy

        mock_play_context = MagicMock()

        mock_shared_loader = MagicMock()
        mock_queue = MagicMock()

        new_stdin = None
        job_vars = dict()

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
        )

        def _execute(variables):
            return dict(item=variables.get('item'))

        te._squash_items = MagicMock(return_value=items)
        te._execute = MagicMock(side_effect=_execute)

        res = te._run_loop(items)
        self.assertEqual(len(res), 3)

    def test_task_executor_squash_items(self):
        items = ['a', 'b', 'c']

        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        loop_var = 'item'

        def _evaluate_conditional(templar, variables):
            item = variables.get(loop_var)
            if item == 'b':
                return False
            return True

        mock_task = MagicMock()
        mock_task.evaluate_conditional.side_effect = _evaluate_conditional

        mock_play_context = MagicMock()

        mock_shared_loader = None
        mock_queue = MagicMock()

        new_stdin = None
        job_vars = dict(pkg_mgr='yum')

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=mock_shared_loader,
            final_q=mock_queue,
        )

        # No replacement
        mock_task.action = 'yum'
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, ['a', 'b', 'c'])
        self.assertIsInstance(mock_task.args, MagicMock)

        mock_task.action = 'foo'
        mock_task.args = {'name': '{{item}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, ['a', 'b', 'c'])
        self.assertEqual(mock_task.args, {'name': '{{item}}'})

        mock_task.action = 'yum'
        mock_task.args = {'name': 'static'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, ['a', 'b', 'c'])
        self.assertEqual(mock_task.args, {'name': 'static'})

        mock_task.action = 'yum'
        mock_task.args = {'name': '{{pkg_mgr}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, ['a', 'b', 'c'])
        self.assertEqual(mock_task.args, {'name': '{{pkg_mgr}}'})

        mock_task.action = '{{unknown}}'
        mock_task.args = {'name': '{{item}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, ['a', 'b', 'c'])
        self.assertEqual(mock_task.args, {'name': '{{item}}'})

        # Could do something like this to recover from bad deps in a package
        job_vars = dict(pkg_mgr='yum', packages=['a', 'b'])
        items = ['absent', 'latest']
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{ packages }}', 'state': '{{ item }}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{ packages }}', 'state': '{{ item }}'})

        # Maybe should raise an error in this case.  The user would have to specify:
        # - yum: name="{{ packages[item] }}"
        #   with_items:
        #     - ['a', 'b']
        #     - ['foo', 'bar']
        # you can't use a list as a dict key so that would probably throw
        # an error later.  If so, we can throw it now instead.
        # Squashing in this case would not be intuitive as the user is being
        # explicit in using each list entry as a key.
        job_vars = dict(pkg_mgr='yum', packages={"a": "foo", "b": "bar", "foo": "baz", "bar": "quux"})
        items = [['a', 'b'], ['foo', 'bar']]
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{ packages[item] }}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{ packages[item] }}'})

        # Replaces
        items = ['a', 'b', 'c']
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{item}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, [['a', 'c']])
        self.assertEqual(mock_task.args, {'name': ['a', 'c']})

        mock_task.action = '{{pkg_mgr}}'
        mock_task.args = {'name': '{{item}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        self.assertEqual(new_items, [['a', 'c']])
        self.assertEqual(mock_task.args, {'name': ['a', 'c']})

        # New loop_var
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{a_loop_var_item}}'}
        mock_task.loop_control = {'loop_var': 'a_loop_var_item'}
        loop_var = 'a_loop_var_item'
        new_items = te._squash_items(items=items, loop_var='a_loop_var_item', variables=job_vars)
        self.assertEqual(new_items, [['a', 'c']])
        self.assertEqual(mock_task.args, {'name': ['a', 'c']})
        loop_var = 'item'

        #
        # These are presently not optimized but could be in the future.
        # Expected output if they were optimized is given as a comment
        # Please move these to a different section if they are optimized
        #

        # Squashing lists
        job_vars = dict(pkg_mgr='yum')
        items = [['a', 'b'], ['foo', 'bar']]
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{ item }}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        # self.assertEqual(new_items, [['a', 'b', 'foo', 'bar']])
        # self.assertEqual(mock_task.args, {'name': ['a', 'b', 'foo', 'bar']})
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{ item }}'})

        # Retrieving from a dict
        items = ['a', 'b', 'foo']
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{ packages[item] }}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        # self.assertEqual(new_items, [['foo', 'baz']])
        # self.assertEqual(mock_task.args, {'name': ['foo', 'baz']})
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{ packages[item] }}'})

        # Another way to retrieve from a dict
        job_vars = dict(pkg_mgr='yum')
        items = [{'package': 'foo'}, {'package': 'bar'}]
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{ item["package"] }}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        # self.assertEqual(new_items, [['foo', 'bar']])
        # self.assertEqual(mock_task.args, {'name': ['foo', 'bar']})
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{ item["package"] }}'})

        items = [
            dict(name='a', state='present'),
            dict(name='b', state='present'),
            dict(name='c', state='present'),
        ]
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{item.name}}', 'state': '{{item.state}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        # self.assertEqual(new_items, [dict(name=['a', 'b', 'c'], state='present')])
        # self.assertEqual(mock_task.args, {'name': ['a', 'b', 'c'], 'state': 'present'})
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{item.name}}', 'state': '{{item.state}}'})

        items = [
            dict(name='a', state='present'),
            dict(name='b', state='present'),
            dict(name='c', state='absent'),
        ]
        mock_task.action = 'yum'
        mock_task.args = {'name': '{{item.name}}', 'state': '{{item.state}}'}
        new_items = te._squash_items(items=items, loop_var='item', variables=job_vars)
        # self.assertEqual(new_items, [dict(name=['a', 'b'], state='present'),
        #         dict(name='c', state='absent')])
        # self.assertEqual(mock_task.args, {'name': '{{item.name}}', 'state': '{{item.state}}'})
        self.assertEqual(new_items, items)
        self.assertEqual(mock_task.args, {'name': '{{item.name}}', 'state': '{{item.state}}'})

    def test_task_executor_execute(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task.args = dict()
        mock_task.retries = 0
        mock_task.delay = -1
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

        mock_play_context = MagicMock()
        mock_play_context.post_validate.return_value = None
        mock_play_context.update_vars.return_value = None

        mock_connection = MagicMock()
        mock_connection.set_host_overrides.return_value = None
        mock_connection._connect.return_value = None

        mock_action = MagicMock()
        mock_queue = MagicMock()

        shared_loader = None
        new_stdin = None
        job_vars = dict(omit="XXXXXXXXXXXXXXXXXXX")

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=shared_loader,
            final_q=mock_queue,
        )

        te._get_connection = MagicMock(return_value=mock_connection)
        te._get_action_handler = MagicMock(return_value=mock_action)

        mock_action.run.return_value = dict(ansible_facts=dict())
        res = te._execute()

        mock_task.changed_when = MagicMock(return_value=AnsibleUnicode("1 == 1"))
        res = te._execute()

        mock_task.changed_when = None
        mock_task.failed_when = MagicMock(return_value=AnsibleUnicode("1 == 1"))
        res = te._execute()

        mock_task.failed_when = None
        mock_task.evaluate_conditional.return_value = False
        res = te._execute()

        mock_task.evaluate_conditional.return_value = True
        mock_task.args = dict(_raw_params='foo.yml', a='foo', b='bar')
        mock_task.action = 'include'
        res = te._execute()

    def test_task_executor_poll_async_result(self):
        fake_loader = DictDataLoader({})

        mock_host = MagicMock()

        mock_task = MagicMock()
        mock_task.async_val = 0.1
        mock_task.poll = 0.05

        mock_play_context = MagicMock()

        mock_connection = MagicMock()

        mock_action = MagicMock()
        mock_queue = MagicMock()

        shared_loader = MagicMock()
        shared_loader.action_loader = action_loader

        new_stdin = None
        job_vars = dict(omit="XXXXXXXXXXXXXXXXXXX")

        te = TaskExecutor(
            host=mock_host,
            task=mock_task,
            job_vars=job_vars,
            play_context=mock_play_context,
            new_stdin=new_stdin,
            loader=fake_loader,
            shared_loader_obj=shared_loader,
            final_q=mock_queue,
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

    def test_recursive_remove_omit(self):
        omit_token = 'POPCORN'

        data = {
            'foo': 'bar',
            'baz': 1,
            'qux': ['one', 'two', 'three'],
            'subdict': {
                'remove': 'POPCORN',
                'keep': 'not_popcorn',
                'subsubdict': {
                    'remove': 'POPCORN',
                    'keep': 'not_popcorn',
                },
                'a_list': ['POPCORN'],
            },
            'a_list': ['POPCORN'],
            'list_of_lists': [
                ['some', 'thing'],
            ],
            'list_of_dicts': [
                {
                    'remove': 'POPCORN',
                }
            ],
        }

        expected = {
            'foo': 'bar',
            'baz': 1,
            'qux': ['one', 'two', 'three'],
            'subdict': {
                'keep': 'not_popcorn',
                'subsubdict': {
                    'keep': 'not_popcorn',
                },
                'a_list': ['POPCORN'],
            },
            'a_list': ['POPCORN'],
            'list_of_lists': [
                ['some', 'thing'],
            ],
            'list_of_dicts': [{}],
        }

        self.assertEqual(remove_omit(data, omit_token), expected)
