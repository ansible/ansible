from __future__ import annotations

import errno
import os
import unittest
from unittest.mock import MagicMock, patch

from ansible.executor.process.worker import WorkerPopen


class TestWorkerPopen(unittest.TestCase):

    def test_poll_with_childprocess_error(self):
        """Test that poll() handles ChildProcessError gracefully."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = None

        # Mock os.waitpid to raise ChildProcessError
        with patch('os.waitpid') as mock_waitpid, \
             patch('ansible.executor.process.worker.display') as mock_display:

            mock_waitpid.side_effect = ChildProcessError()

            # Call poll()
            result = worker_popen.poll()

            # Verify display.error was NOT called for ChildProcessError
            mock_display.error.assert_not_called()

            # Verify None is returned
            assert result is None

            # Verify returncode is still None
            assert worker_popen.returncode is None

    def test_poll_success(self):
        """Test that poll() correctly handles successful waitpid."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = None

        # Mock os.waitpid to return successfully
        # waitpid returns (pid, status)
        # Status 0 means exited normally with code 0
        with patch('os.waitpid') as mock_waitpid:
            mock_waitpid.return_value = (12345, 0)

            # Call poll()
            result = worker_popen.poll()

            # Verify waitpid was called with correct arguments
            mock_waitpid.assert_called_once_with(12345, os.WNOHANG)

            # Verify returncode is set to 0
            assert worker_popen.returncode == 0
            assert result == 0

    def test_poll_with_existing_returncode(self):
        """Test that poll() returns existing returncode without calling waitpid."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = 42  # Already has a returncode

        # Mock os.waitpid
        with patch('os.waitpid') as mock_waitpid:
            # Call poll()
            result = worker_popen.poll()

            # Verify waitpid was NOT called
            mock_waitpid.assert_not_called()

            # Verify existing returncode is returned
            assert result == 42

    def test_poll_with_different_pid(self):
        """Test that poll() handles waitpid returning different pid."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = None

        # Mock os.waitpid to return a different pid (shouldn't happen in practice)
        with patch('os.waitpid') as mock_waitpid:
            mock_waitpid.return_value = (99999, 0)

            # Call poll()
            result = worker_popen.poll()

            # Verify returncode is still None (pid didn't match)
            assert worker_popen.returncode is None
            assert result is None

    def test_poll_with_custom_flag(self):
        """Test that poll() accepts and uses custom flag parameter."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = None

        # Mock os.waitpid
        with patch('os.waitpid') as mock_waitpid:
            mock_waitpid.return_value = (12345, 0)

            # Call poll() with custom flag (0 means block until child exits)
            result = worker_popen.poll(flag=0)

            # Verify waitpid was called with custom flag
            mock_waitpid.assert_called_once_with(12345, 0)

            # Verify returncode is set
            assert worker_popen.returncode == 0
            assert result == 0

    def test_poll_with_nonzero_exit_status(self):
        """Test that poll() correctly converts non-zero exit status."""
        # Create a mock process object
        mock_process = MagicMock()
        mock_process.pid = 12345

        # Create WorkerPopen instance
        worker_popen = WorkerPopen(mock_process)
        worker_popen.pid = 12345
        worker_popen.returncode = None

        # Mock os.waitpid to return exit status 1
        # On Unix, exit code 1 is represented as status 256 (1 << 8)
        with patch('os.waitpid') as mock_waitpid:
            mock_waitpid.return_value = (12345, 256)

            # Call poll()
            result = worker_popen.poll()

            # Verify returncode is set to 1
            assert worker_popen.returncode == 1
            assert result == 1

    def test_poll_with_various_oserrors(self):
        """Test that poll() handles various OSError types correctly."""
        test_cases = [
            (errno.EINTR, "Interrupted system call"),
            (errno.EAGAIN, "Resource temporarily unavailable"),
            (errno.ENOMEM, "Cannot allocate memory"),
        ]

        for error_code, error_msg in test_cases:
            with self.subTest(error_code=error_code, error_msg=error_msg):
                # Create a mock process object
                mock_process = MagicMock()
                mock_process.pid = 12345

                # Create WorkerPopen instance
                worker_popen = WorkerPopen(mock_process)
                worker_popen.pid = 12345
                worker_popen.returncode = None

                # Mock os.waitpid to raise specific OSError
                with patch('os.waitpid') as mock_waitpid, \
                     patch('ansible.executor.process.worker.display') as mock_display:

                    mock_waitpid.side_effect = OSError(error_code, error_msg)

                    # Call poll()
                    result = worker_popen.poll()

                    # Verify display.error was called
                    mock_display.error.assert_called_once()
                    error_log_msg = mock_display.error.call_args[0][0]
                    assert "poll error" in error_log_msg
                    assert "PID 12345" in error_log_msg
                    assert error_msg in error_log_msg

                    # Verify None is returned
                    assert result is None

                    # Verify returncode is still None
                    assert worker_popen.returncode is None
