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

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from ansible.executor.task_result import _RawTaskResult


class TestRawTaskResult(unittest.TestCase):
    def test_task_result_basic(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test loading a result with a dict
        tr = _RawTaskResult(mock_host, mock_task, {}, {})

    def test_task_result_is_changed(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no changed in result
        tr = _RawTaskResult(mock_host, mock_task, {}, {})
        self.assertFalse(tr.is_changed())

        # test with changed in the result
        tr = _RawTaskResult(mock_host, mock_task, dict(changed=True), {})
        self.assertTrue(tr.is_changed())

        # test with multiple results but none changed
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]), {})
        self.assertFalse(tr.is_changed())

        # test with multiple results and one changed
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(changed=False), dict(changed=True), dict(some_key=False)]), {})
        self.assertTrue(tr.is_changed())

    def test_task_result_is_skipped(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no skipped in result
        tr = _RawTaskResult(mock_host, mock_task, dict(), {})
        self.assertFalse(tr.is_skipped())

        # test with skipped in the result
        tr = _RawTaskResult(mock_host, mock_task, dict(skipped=True), {})
        self.assertTrue(tr.is_skipped())

        # test with multiple results but none skipped
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]), {})
        self.assertFalse(tr.is_skipped())

        # test with multiple results and one skipped
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(skipped=False), dict(skipped=True), dict(some_key=False)]), {})
        self.assertFalse(tr.is_skipped())

        # test with multiple results and all skipped
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(skipped=True), dict(skipped=True), dict(skipped=True)]), {})
        self.assertTrue(tr.is_skipped())

        # test with multiple squashed results (list of strings)
        # first with the main result having skipped=False
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=["a", "b", "c"], skipped=False), {})
        self.assertFalse(tr.is_skipped())
        # then with the main result having skipped=True
        tr = _RawTaskResult(mock_host, mock_task, dict(results=["a", "b", "c"], skipped=True), {})
        self.assertTrue(tr.is_skipped())

    def test_task_result_is_unreachable(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no unreachable in result
        tr = _RawTaskResult(mock_host, mock_task, {}, {})
        self.assertFalse(tr.is_unreachable())

        # test with unreachable in the result
        tr = _RawTaskResult(mock_host, mock_task, dict(unreachable=True), {})
        self.assertTrue(tr.is_unreachable())

        # test with multiple results but none unreachable
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(foo='bar'), dict(bam='baz'), True]), {})
        self.assertFalse(tr.is_unreachable())

        # test with multiple results and one unreachable
        mock_task.loop = 'foo'
        tr = _RawTaskResult(mock_host, mock_task, dict(results=[dict(unreachable=False), dict(unreachable=True), dict(some_key=False)]), {})
        self.assertTrue(tr.is_unreachable())

    def test_task_result_is_failed(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # test with no failed in result
        tr = _RawTaskResult(mock_host, mock_task, dict(), {})
        self.assertFalse(tr.is_failed())

        # test failed result with rc values (should not matter)
        tr = _RawTaskResult(mock_host, mock_task, dict(rc=0), {})
        self.assertFalse(tr.is_failed())
        tr = _RawTaskResult(mock_host, mock_task, dict(rc=1), {})
        self.assertFalse(tr.is_failed())

        # test with failed in result
        tr = _RawTaskResult(mock_host, mock_task, dict(failed=True), {})
        self.assertTrue(tr.is_failed())

        # test with failed_when in result
        tr = _RawTaskResult(mock_host, mock_task, dict(failed_when_result=True), {})
        self.assertTrue(tr.is_failed())

    def test_task_result_no_log(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # no_log should remove secrets
        tr = _RawTaskResult(mock_host, mock_task, dict(_ansible_no_log=True, secret='DONTSHOWME'), {})
        clean = tr.as_callback_task_result()
        self.assertTrue('secret' not in clean.result)

    def test_task_result_no_log_preserve(self):
        mock_host = MagicMock()
        mock_task = MagicMock()

        # no_log should not remove preserved keys
        tr = _RawTaskResult(
            mock_host,
            mock_task,
            dict(
                _ansible_no_log=True,
                retries=5,
                attempts=5,
                changed=False,
                foo='bar',
            ),
            task_fields={},
        )
        clean = tr.as_callback_task_result()
        self.assertTrue('retries' in clean.result)
        self.assertTrue('attempts' in clean.result)
        self.assertTrue('changed' in clean.result)
        self.assertTrue('foo' not in clean.result)
