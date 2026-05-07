from __future__ import annotations

import signal

import pytest

from ansible.executor.task_queue_manager import TaskQueueManager


class TestTQMSignalHandler:
    @pytest.mark.parametrize("signum,signame", [
        (signal.SIGTERM, signal.strsignal(signal.SIGTERM)),
        (signal.SIGINT, signal.strsignal(signal.SIGINT)),
    ])
    def test_signal_handler_detects_child_process_race_condition(self, mocker, signum, signame):
        """
        Test that the signal handler detects when called from a forked child.

        This tests the race condition where a forked child receives SIGTERM/SIGINT
        before the inherited handlers from the parent have been replaced.
        When os.getpid() matches a worker PID, we're in the child and should
        return early without attempting worker management.
        """
        mock_inventory = mocker.Mock()
        mock_var_manager = mocker.Mock()
        mock_loader = mocker.Mock()

        mocker.patch('ansible.executor.task_queue_manager.FinalQueue')
        mocker.patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance')
        mocker.patch('ansible.executor.task_queue_manager.context.CLIARGS', {})

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=mock_loader,
            passwords={},
        )

        # Create mock workers
        mock_worker1 = mocker.Mock()
        mock_worker1.pid = 12345
        mock_worker2 = mocker.Mock()
        mock_worker2.pid = 67890

        tqm._workers = [mock_worker1, mock_worker2]

        # Mock os.getpid() to return a worker PID (simulate being in child process)
        mock_getpid = mocker.patch('ansible.executor.task_queue_manager.os.getpid')
        mock_getpid.return_value = 12345

        mock_display = mocker.patch('ansible.executor.task_queue_manager.display')
        mocker.patch('ansible.executor.task_queue_manager.signal.signal')
        mock_os_kill = mocker.patch('ansible.executor.task_queue_manager.os.kill')

        # Call signal handler
        tqm._signal_handler(signum, None)

        # Verify error was logged with correct signal number and name
        mock_display.error.assert_called_once()
        error_msg = mock_display.error.call_args[0][0]
        assert f'Worker PID 12345 received signal "{signum}: {signame}" before detachment' in error_msg

        # Verify no workers were signaled (early return)
        assert not mock_os_kill.called

    def test_signal_handler_normal_operation(self, mocker):
        """Test signal handler in a normal parent process operation."""
        mock_inventory = mocker.Mock()
        mock_var_manager = mocker.Mock()
        mock_loader = mocker.Mock()

        mocker.patch('ansible.executor.task_queue_manager.FinalQueue')
        mocker.patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance')
        mocker.patch('ansible.executor.task_queue_manager.context.CLIARGS', {})

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=mock_loader,
            passwords={},
        )

        # Create an alive mock worker
        mock_worker = mocker.Mock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True

        tqm._workers = [mock_worker]

        # Mock os.getpid() to return a PID that's NOT a worker (normal parent case)
        mock_getpid = mocker.patch('ansible.executor.task_queue_manager.os.getpid')
        mock_getpid.return_value = 99999

        mock_display = mocker.patch('ansible.executor.task_queue_manager.display')
        mocker.patch('ansible.executor.task_queue_manager.signal.signal')
        mock_os_kill = mocker.patch('ansible.executor.task_queue_manager.os.kill')

        # Call signal handler
        tqm._signal_handler(signal.SIGTERM, None)

        # Verify no race condition error was logged
        mock_display.error.assert_not_called()

        # Verify worker was signaled
        kill_calls = [call for call in mock_os_kill.call_args_list if call[0][0] == 12345]
        assert len(kill_calls) == 1
        assert kill_calls[0][0] == (12345, signal.SIGTERM)

    def test_signal_handler_skips_none_workers(self, mocker):
        """Test that None workers don't cause issues."""
        mock_inventory = mocker.Mock()
        mock_var_manager = mocker.Mock()
        mock_loader = mocker.Mock()

        mocker.patch('ansible.executor.task_queue_manager.FinalQueue')
        mocker.patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance')
        mocker.patch('ansible.executor.task_queue_manager.context.CLIARGS', {})

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=mock_loader,
            passwords={},
        )

        # Mix of None and real workers
        mock_worker = mocker.Mock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True

        tqm._workers = [None, mock_worker, None]

        mock_getpid = mocker.patch('ansible.executor.task_queue_manager.os.getpid')
        mock_getpid.return_value = 99999

        mocker.patch('ansible.executor.task_queue_manager.display')
        mocker.patch('ansible.executor.task_queue_manager.signal.signal')
        mock_os_kill = mocker.patch('ansible.executor.task_queue_manager.os.kill')

        # Should not crash
        tqm._signal_handler(signal.SIGTERM, None)

        # Verify worker was signaled
        kill_calls = [call for call in mock_os_kill.call_args_list if call[0][0] == 12345]
        assert len(kill_calls) == 1

    def test_signal_handler_skips_dead_workers(self, mocker):
        """Test that dead workers are skipped."""
        mock_inventory = mocker.Mock()
        mock_var_manager = mocker.Mock()
        mock_loader = mocker.Mock()

        mocker.patch('ansible.executor.task_queue_manager.FinalQueue')
        mocker.patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance')
        mocker.patch('ansible.executor.task_queue_manager.context.CLIARGS', {})

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=mock_loader,
            passwords={},
        )

        # Create a dead worker
        mock_worker = mocker.Mock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = False

        tqm._workers = [mock_worker]

        mock_getpid = mocker.patch('ansible.executor.task_queue_manager.os.getpid')
        mock_getpid.return_value = 99999

        mocker.patch('ansible.executor.task_queue_manager.display')
        mocker.patch('ansible.executor.task_queue_manager.signal.signal')
        mock_os_kill = mocker.patch('ansible.executor.task_queue_manager.os.kill')

        tqm._signal_handler(signal.SIGTERM, None)

        # Verify dead worker was NOT signaled
        kill_calls = [call for call in mock_os_kill.call_args_list if call[0][0] == 12345]
        assert len(kill_calls) == 0

    def test_signal_handler_with_sigint_raises_keyboard_interrupt(self, mocker):
        """Test that SIGINT raises KeyboardInterrupt after handling."""
        mock_inventory = mocker.Mock()
        mock_var_manager = mocker.Mock()
        mock_loader = mocker.Mock()

        mocker.patch('ansible.executor.task_queue_manager.FinalQueue')
        mocker.patch('ansible.executor.task_queue_manager._rpc_host.LocalManager.shared_instance')
        mocker.patch('ansible.executor.task_queue_manager.context.CLIARGS', {})

        tqm = TaskQueueManager(
            inventory=mock_inventory,
            variable_manager=mock_var_manager,
            loader=mock_loader,
            passwords={},
        )

        mock_worker = mocker.Mock()
        mock_worker.pid = 12345
        mock_worker.is_alive.return_value = True

        tqm._workers = [mock_worker]

        mock_getpid = mocker.patch('ansible.executor.task_queue_manager.os.getpid')
        mock_getpid.return_value = 99999

        mocker.patch('ansible.executor.task_queue_manager.display')
        mocker.patch('ansible.executor.task_queue_manager.signal.signal')
        mocker.patch('ansible.executor.task_queue_manager.os.kill')

        # SIGINT should raise KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            tqm._signal_handler(signal.SIGINT, None)
