# (c) 2016, James Cammarata <jimi@sngx.net>
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

from ansible.executor.task_result import TaskResult


class TestTaskResult(unittest.TestCase):
    def test_task_result_basic(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test loading a result with a dict
        tr = TaskResult(mock_host, mock_task, dict())

        # test loading a result with a JSON string
        with patch('ansible.parsing.dataloader.DataLoader.load') as p:
            tr = TaskResult(mock_host, mock_task, '{}')

    def test_task_result_is_changed(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no changed in result
        tr = TaskResult(mock_host, mock_task, dict())
        self.assertFalse(tr.is_changed())

        # test with changed in the result
        tr = TaskResult(mock_host, mock_task, dict(changed=True))
        self.assertTrue(tr.is_changed())

        # test with multiple results but none changed
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]))
        self.assertFalse(tr.is_changed())

        # test with multiple results and one changed
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(changed=False), dict(changed=True), dict(some_key=False)]))
        self.assertTrue(tr.is_changed())

    def test_task_result_is_skipped(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no skipped in result
        tr = TaskResult(mock_host, mock_task, dict())
        self.assertFalse(tr.is_skipped())

        # test with skipped in the result
        tr = TaskResult(mock_host, mock_task, dict(skipped=True))
        self.assertTrue(tr.is_skipped())

        # test with multiple results but none skipped
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]))
        self.assertFalse(tr.is_skipped())

        # test with multiple results and one skipped
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(skipped=False), dict(skipped=True), dict(some_key=False)]))
        self.assertFalse(tr.is_skipped())

        # test with multiple results and all skipped
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(skipped=True), dict(skipped=True), dict(skipped=True)]))
        self.assertTrue(tr.is_skipped())

        # test with multiple squashed results (list of strings)
        # first with the main result having skipped=False
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=["a", "b", "c"], skipped=False))
        self.assertFalse(tr.is_skipped())
        # then with the main result having skipped=True
        tr = TaskResult(mock_host, mock_task, dict(results=["a", "b", "c"], skipped=True))
        self.assertTrue(tr.is_skipped())

    def test_task_result_is_unreachable(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no unreachable in result
        tr = TaskResult(mock_host, mock_task, dict())
        self.assertFalse(tr.is_unreachable())

        # test with unreachable in the result
        tr = TaskResult(mock_host, mock_task, dict(unreachable=True))
        self.assertTrue(tr.is_unreachable())

        # test with multiple results but none unreachable
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]))
        self.assertFalse(tr.is_unreachable())

        # test with multiple results and one unreachable
        mock_task.loop = 'foo'
        tr = TaskResult(mock_host, mock_task, dict(results=[dict(unreachable=False), dict(unreachable=True), dict(some_key=False)]))
        self.assertTrue(tr.is_unreachable())

    def test_task_result_is_failed(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no failed in result
        tr = TaskResult(mock_host, mock_task, dict())
        self.assertFalse(tr.is_failed())

        # test failed result with rc values (should not matter)
        tr = TaskResult(mock_host, mock_task, dict(rc=0))
        self.assertFalse(tr.is_failed())
        tr = TaskResult(mock_host, mock_task, dict(rc=1))
        self.assertFalse(tr.is_failed())

        # test with failed in result
        tr = TaskResult(mock_host, mock_task, dict(failed=True))
        self.assertTrue(tr.is_failed())

        # test with failed_when in result
        tr = TaskResult(mock_host, mock_task, dict(failed_when_result=True))
        self.assertTrue(tr.is_failed())

    def test_task_result_no_log(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # no_log should remove secrets
        tr = TaskResult(mock_host, mock_task, dict(_ansible_no_log=True, secret='DONTSHOWME'))
        clean = tr.clean_copy()
        self.assertTrue('secret' not in clean._result)

    def test_task_result_no_log_preserve(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # no_log should not remove presrved keys
        tr = TaskResult(
            mock_host,
            mock_task,
            dict(
                _ansible_no_log=True,
                retries=5,
                attempts=5,
                changed=False,
                foo='bar',
            )
        )
        clean = tr.clean_copy()
        self.assertTrue('retries' in clean._result)
        self.assertTrue('attempts' in clean._result)
        self.assertTrue('changed' in clean._result)
        self.assertTrue('foo' not in clean._result)
