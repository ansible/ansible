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

import signal
from unittest.mock import MagicMock, patch

import pytest

from ansible.executor.task_queue_manager import TaskQueueManager


@pytest.fixture()
def tqm():
    with (
        patch('ansible.executor.task_queue_manager.FinalQueue'),
        patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance'),
        patch('ansible.executor.task_queue_manager.context.CLIARGS', {}),
    ):
        return TaskQueueManager(
            inventory=MagicMock(),
            variable_manager=MagicMock(),
            loader=MagicMock(),
            passwords={},
        )


class TestSignalHandlerChildRaceDetection:
    """Tests for the race condition where a forked child receives a signal
    before it has replaced the inherited parent signal handlers."""

    @pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGINT])
    def test_child_process_skips_worker_management(self, tqm, signum):
        """When the handler runs in a child (os.getpid() matches a worker PID),
        it must not call worker.is_alive() or attempt to signal other workers."""
        mock_worker = MagicMock()
        mock_worker.pid = 12345
        tqm._workers = [mock_worker]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=12345),
            patch('ansible.executor.task_queue_manager.os.kill') as mock_kill,
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            tqm._signal_handler(signum, None)

        mock_worker.is_alive.assert_not_called()
        mock_kill.assert_called_once_with(12345, signum)

    def test_child_race_skips_none_workers(self, tqm):
        """None entries in the worker list must not cause errors during the
        child-detection check."""
        mock_worker = MagicMock()
        mock_worker.pid = 42
        tqm._workers = [None, mock_worker, None]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=42),
            patch('ansible.executor.task_queue_manager.os.kill') as mock_kill,
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            tqm._signal_handler(signal.SIGTERM, None)

        mock_worker.is_alive.assert_not_called()
        mock_kill.assert_called_once_with(42, signal.SIGTERM)


class TestSignalHandlerNormalOperation:
    """Tests for normal parent-process signal handling (no race condition)."""

    def test_signals_alive_workers(self, tqm):
        mock_worker = MagicMock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True
        tqm._workers = [mock_worker]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=99999),
            patch('ansible.executor.task_queue_manager.os.kill') as mock_kill,
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            tqm._signal_handler(signal.SIGTERM, None)

        worker_calls = [c for c in mock_kill.call_args_list if c[0][0] == 12345]
        assert len(worker_calls) == 1
        assert worker_calls[0][0] == (12345, signal.SIGTERM)

    def test_skips_dead_workers(self, tqm):
        mock_worker = MagicMock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = False
        tqm._workers = [mock_worker]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=99999),
            patch('ansible.executor.task_queue_manager.os.kill') as mock_kill,
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            tqm._signal_handler(signal.SIGTERM, None)

        worker_calls = [c for c in mock_kill.call_args_list if c[0][0] == 12345]
        assert len(worker_calls) == 0

    def test_skips_none_workers(self, tqm):
        mock_worker = MagicMock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True
        tqm._workers = [None, mock_worker, None]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=99999),
            patch('ansible.executor.task_queue_manager.os.kill') as mock_kill,
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            tqm._signal_handler(signal.SIGTERM, None)

        worker_calls = [c for c in mock_kill.call_args_list if c[0][0] == 12345]
        assert len(worker_calls) == 1

    def test_sigint_raises_keyboard_interrupt(self, tqm):
        mock_worker = MagicMock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True
        tqm._workers = [mock_worker]

        with (
            patch('ansible.executor.task_queue_manager.os.getpid', return_value=99999),
            patch('ansible.executor.task_queue_manager.os.kill'),
            patch('ansible.executor.task_queue_manager.signal.signal'),
        ):
            with pytest.raises(KeyboardInterrupt):
                tqm._signal_handler(signal.SIGINT, None)


class TestResetChildSignals:
    def test_resets_sigterm_and_sigint(self):
        with patch('ansible.executor.task_queue_manager.signal.signal') as mock_signal:
            TaskQueueManager._reset_child_signals()

        mock_signal.assert_any_call(signal.SIGTERM, signal.SIG_DFL)
        mock_signal.assert_any_call(signal.SIGINT, signal.SIG_DFL)
        assert mock_signal.call_count == 2
