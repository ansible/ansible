#
# (c) 2020 Red Hat Inc.
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

from io import StringIO

import os
import unittest
from subprocess import TimeoutExpired
from unittest.mock import MagicMock, patch

from ansible.errors import AnsibleError
from ansible.plugins.connection import local
from ansible.playbook.play_context import PlayContext


class TestLocalConnectionClass(unittest.TestCase):

    def test_local_connection_module(self):
        play_context = PlayContext()
        play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        in_stream = StringIO()

        self.assertIsInstance(local.Connection(play_context, in_stream), local.Connection)


class TestLocalBecomeCleanup(unittest.TestCase):
    """Resources owned by exec_command must not escape on become failure."""

    def _connection(self, become=None):
        conn = local.Connection(PlayContext(), StringIO())
        conn.set_option('pipelining', False)
        conn.cwd = None
        if become is not None:
            conn.set_become_plugin(become)
        return conn

    def _become(self, expect_prompt=False):
        become = MagicMock()
        become._id = 'testid'
        become.expect_prompt.return_value = expect_prompt
        return become

    def _popen(self):
        popen = MagicMock()
        popen.poll.return_value = None
        popen.communicate.return_value = (b'out', b'err')
        popen.returncode = 0
        return popen

    def test_become_failure_reaps_and_closes(self):
        """T1: become handshake raise must terminate/wait/close the child."""
        failure = AnsibleError('Premature end of stream')
        popen = self._popen()
        conn = self._connection(self._become())
        with patch.object(local.subprocess, 'Popen', return_value=popen), \
                patch.object(local.Connection, '_ensure_become_success', side_effect=failure) as handshake:
            with self.assertRaises(AnsibleError) as ctx:
                conn.exec_command('echo hi', sudoable=True)
        self.assertIs(ctx.exception, failure)
        handshake.assert_called_once()
        popen.terminate.assert_called_once_with()
        popen.wait.assert_called()
        popen.stdout.close.assert_called_once_with()
        popen.stderr.close.assert_called_once_with()

    def test_become_failure_kill_fallback(self):
        """T2: a child ignoring terminate must be killed and reaped."""
        popen = self._popen()
        popen.wait.side_effect = [TimeoutExpired('echo hi', 10), 0]
        conn = self._connection(self._become())
        with patch.object(local.subprocess, 'Popen', return_value=popen), \
                patch.object(local.Connection, '_ensure_become_success', side_effect=AnsibleError('Timed out')):
            with self.assertRaises(AnsibleError):
                conn.exec_command('echo hi', sudoable=True)
        popen.terminate.assert_called_once_with()
        popen.kill.assert_called_once_with()
        self.assertEqual(popen.wait.call_count, 2)

    def test_success_path_unchanged(self):
        """T3: normal completion keeps output/returncode, no terminate."""
        popen = self._popen()
        popen.poll.return_value = 0
        conn = self._connection(self._become())
        with patch.object(local.subprocess, 'Popen', return_value=popen), \
                patch.object(local.Connection, '_ensure_become_success', return_value=(b'pre-out', b'pre-err')):
            self.assertEqual(
                conn.exec_command('echo hi', sudoable=True),
                (0, b'pre-outout', b'pre-errerr'),
            )
        popen.terminate.assert_not_called()
        popen.kill.assert_not_called()

    def test_no_become_path_unchanged(self):
        """T4: become=None still returns real handshake output untouched."""
        popen = self._popen()
        popen.poll.return_value = 0
        conn = self._connection(None)
        with patch.object(local.subprocess, 'Popen', return_value=popen):
            self.assertEqual(
                conn.exec_command('echo hi', sudoable=True),
                (0, b'out', b'err'),
            )
        popen.terminate.assert_not_called()
        popen.kill.assert_not_called()

    def test_pty_fds_closed_on_become_failure(self):
        """T5: both owned PTY descriptors are closed exactly once."""
        closed = []
        real_close = os.close

        def counting_close(fd):
            closed.append(fd)
            return real_close(fd)

        primary, secondary = os.pipe()
        popen = self._popen()
        conn = self._connection(self._become(expect_prompt=True))
        with patch.object(local.pty, 'openpty', return_value=(primary, secondary)), \
                patch.object(local.subprocess, 'Popen', return_value=popen), \
                patch.object(local.Connection, '_ensure_become_success', side_effect=AnsibleError('boom')), \
                patch.object(local.os, 'close', side_effect=counting_close):
            with self.assertRaises(AnsibleError):
                conn.exec_command('echo hi', sudoable=True)
        self.assertEqual(sorted(closed), sorted([primary, secondary]))
        for fd in (primary, secondary):
            with self.assertRaises(OSError):
                os.fstat(fd)

    def test_popen_failure_closes_pty(self):
        """T6: PTY cleaned up when Popen itself raises (partial init)."""
        primary, secondary = os.pipe()
        conn = self._connection(self._become(expect_prompt=True))
        with patch.object(local.pty, 'openpty', return_value=(primary, secondary)), \
                patch.object(local.subprocess, 'Popen', side_effect=OSError('nope')):
            with self.assertRaises(OSError):
                conn.exec_command('echo hi', sudoable=True)
        for fd in (primary, secondary):
            with self.assertRaises(OSError):
                os.fstat(fd)
