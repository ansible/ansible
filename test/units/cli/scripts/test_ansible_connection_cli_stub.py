# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import io
import json
import os
import pickle
import socket

import pytest

from contextlib import nullcontext as _nullcontext
from unittest.mock import MagicMock, patch

from ansible.cli.scripts import ansible_connection_cli_stub as stub
from ansible.module_utils.connection import ConnectionError


def _frame(obj):
    data = pickle.dumps(obj)
    return b'%d\n' % len(data) + data


def _fake_stdin(options, play_context_data):
    stream = io.BytesIO(_frame(options) + _frame(play_context_data))
    return MagicMock(buffer=stream)


class _FakeSSH:
    @staticmethod
    def _create_control_path(host, port, user, connection=None, pid=None):
        return '%(directory)s/pc-sock'


def _transport_error(message):
    error = ConnectionError(message)
    error.__cause__ = ConnectionRefusedError('Connection refused')
    return error


def _decode_error(message):
    return ConnectionError(message)


def _make_connection_class(instances, set_options_error=None, update_play_context_error=None):
    class _FakeConnection:
        def __init__(self, socket_path):
            self.socket_path = socket_path
            instances.append(self)

        def set_options(self, direct=None):
            if set_options_error is not None:
                raise set_options_error

        def update_play_context(self, play_context_data):
            if update_play_context_error is not None:
                raise update_play_context_error

        def set_check_prompt(self, task_uuid):
            pass

        def pop_messages(self):
            return []

    return _FakeConnection


def _run_main(tmp_path, fake_connection_class, fork=None, pipe_fds=None):
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    fork_patch = patch.object(stub, 'fork_process', fork) if fork is not None else patch.object(stub, 'fork_process')
    pipe_patch = patch('os.pipe', return_value=pipe_fds) if pipe_fds is not None else _nullcontext()
    with (
        patch.object(stub, 'Connection', fake_connection_class),
        patch.object(stub, 'connection_loader') as mock_loader,
        patch.object(stub, 'init_plugin_loader', lambda: None),
        fork_patch as mock_fork,
        patch.object(stub.C, 'PERSISTENT_CONTROL_PATH_DIR', str(tmp_path)),
        patch('sys.stdin', _fake_stdin({}, {})),
        patch('sys.stdout', captured_stdout),
        patch('sys.stderr', captured_stderr),
        pipe_patch,
    ):
        mock_loader.get.return_value = _FakeSSH
        with pytest.raises(SystemExit) as excinfo:
            stub.main(['ansible-connection', '123', 'task-uuid'])
    output = captured_stdout.getvalue() or captured_stderr.getvalue()
    return excinfo.value.code, json.loads(output), mock_fork


def _socket_file_id(socket_path):
    path_stat = os.stat(socket_path)
    return (path_stat.st_dev, path_stat.st_ino)


def _run_main_starting_fresh_daemon(tmp_path, socket_path, fake_connection_class, assert_socket_gone=True):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, json.dumps({'messages': [], 'socket_path': str(socket_path)}).encode())

    def spawn_daemon():
        if assert_socket_gone:
            assert not os.path.exists(socket_path)
        return 1234

    code, result, mock_fork = _run_main(
        tmp_path,
        fake_connection_class,
        fork=MagicMock(side_effect=spawn_daemon),
        pipe_fds=(read_fd, write_fd),
    )
    return code, result, mock_fork


class _FakePluginConnection:
    def __init__(self):
        self.closed = False
        self.saw_socket_file = None
        self.connected_at_close = None
        self.socket_path_at_close = None
        self.close_error = None

    def get_option(self, name):
        return False

    def close(self):
        self.saw_socket_file = os.path.exists(self.socket_path)
        self.connected_at_close = getattr(self, '_connected', None)
        self.socket_path_at_close = getattr(self, '_socket_path', None)
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


def test_shutdown_unlinks_socket_before_closing_connection(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = listener
    process._socket_file_id = _socket_file_id(socket_path)
    fake_connection = _FakePluginConnection()
    fake_connection.socket_path = str(socket_path)
    process.connection = fake_connection

    process.shutdown()

    assert fake_connection.closed
    assert fake_connection.saw_socket_file is False
    assert not os.path.exists(socket_path)
    assert listener.fileno() == -1


def test_shutdown_without_socket_file_is_a_noop(tmp_path):
    process = stub.ConnectionProcess(None, None, str(tmp_path / 'pc-sock'), str(tmp_path))

    process.shutdown()


def test_main_reuse_stale_daemon_starts_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances, set_options_error=_transport_error('Unable to connect to socket %r.' % str(socket_path))
    )

    read_fd, write_fd = os.pipe()
    os.write(write_fd, json.dumps({'messages': [], 'socket_path': str(socket_path)}).encode())

    def spawn_daemon():
        assert not os.path.exists(socket_path)
        return 1234

    captured_stdout = io.StringIO()
    with (
        patch.object(stub, 'Connection', fake_connection_class),
        patch.object(stub, 'connection_loader') as mock_loader,
        patch.object(stub, 'init_plugin_loader', lambda: None),
        patch.object(stub, 'fork_process', side_effect=spawn_daemon) as mock_fork,
        patch('os.pipe', return_value=(read_fd, write_fd)),
        patch.object(stub.C, 'PERSISTENT_CONTROL_PATH_DIR', str(tmp_path)),
        patch('sys.stdin', _fake_stdin({}, {})),
        patch('sys.stdout', captured_stdout),
    ):
        mock_loader.get.return_value = _FakeSSH
        with pytest.raises(SystemExit) as excinfo:
            stub.main(['ansible-connection', '123', 'task-uuid'])

    assert excinfo.value.code == 0
    mock_fork.assert_called_once()
    result = json.loads(captured_stdout.getvalue())
    assert 'error' not in result
    assert 'exception' not in result
    assert result['socket_path'] == str(socket_path)


def test_main_reuse_live_daemon_does_not_start_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(instances)

    captured_stdout = io.StringIO()
    with (
        patch.object(stub, 'Connection', fake_connection_class),
        patch.object(stub, 'connection_loader') as mock_loader,
        patch.object(stub, 'init_plugin_loader', lambda: None),
        patch.object(stub, 'fork_process') as mock_fork,
        patch.object(stub.C, 'PERSISTENT_CONTROL_PATH_DIR', str(tmp_path)),
        patch('sys.stdin', _fake_stdin({}, {})),
        patch('sys.stdout', captured_stdout),
    ):
        mock_loader.get.return_value = _FakeSSH
        with pytest.raises(SystemExit) as excinfo:
            stub.main(['ansible-connection', '123', 'task-uuid'])

    assert excinfo.value.code == 0
    mock_fork.assert_not_called()
    result = json.loads(captured_stdout.getvalue())
    assert 'error' not in result
    assert 'exception' not in result
    assert result['socket_path'] == str(socket_path)


def test_main_probe_decode_error_propagates_without_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances, set_options_error=_decode_error('Unable to decode JSON from response to set_options.')
    )

    captured_stdout = io.StringIO()
    with (
        patch.object(stub, 'Connection', fake_connection_class),
        patch.object(stub, 'connection_loader') as mock_loader,
        patch.object(stub, 'init_plugin_loader', lambda: None),
        patch.object(stub, 'fork_process') as mock_fork,
        patch.object(stub.C, 'PERSISTENT_CONTROL_PATH_DIR', str(tmp_path)),
        patch('sys.stdin', _fake_stdin({}, {})),
        patch('sys.stdout', captured_stdout),
    ):
        mock_loader.get.return_value = _FakeSSH
        with pytest.raises(ConnectionError, match='Unable to decode JSON'):
            stub.main(['ansible-connection', '123', 'task-uuid'])

    mock_fork.assert_not_called()


def test_main_probe_missing_socket_message_starts_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances,
        set_options_error=_decode_error('socket path %s does not exist or cannot be found.' % str(socket_path)),
    )

    code, result, mock_fork = _run_main_starting_fresh_daemon(tmp_path, socket_path, fake_connection_class)

    assert code == 0
    mock_fork.assert_called_once()
    assert 'error' not in result
    assert 'exception' not in result
    assert result['socket_path'] == str(socket_path)


def test_main_update_play_context_transport_error_starts_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances, update_play_context_error=_transport_error('Unable to connect to socket %r.' % str(socket_path))
    )

    code, result, mock_fork = _run_main_starting_fresh_daemon(tmp_path, socket_path, fake_connection_class)

    assert code == 0
    mock_fork.assert_called_once()
    assert 'error' not in result
    assert 'exception' not in result
    assert result['socket_path'] == str(socket_path)


def test_main_update_play_context_decode_error_fails_without_fresh_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances,
        update_play_context_error=_decode_error('Unable to decode JSON from response to update_play_context.'),
    )

    code, result, mock_fork = _run_main(tmp_path, fake_connection_class)

    assert code == 1
    mock_fork.assert_not_called()
    assert 'error' in result
    assert 'exception' in result


def test_main_probe_stale_socket_remove_failure_is_recorded(tmp_path, monkeypatch):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()
    instances = []
    fake_connection_class = _make_connection_class(
        instances, set_options_error=_transport_error('Unable to connect to socket %r.' % str(socket_path))
    )

    real_remove = os.remove

    def remove_side_effect(path):
        if str(path) == str(socket_path):
            raise PermissionError('Permission denied')
        return real_remove(path)

    monkeypatch.setattr(os, 'remove', remove_side_effect)

    code, result, mock_fork = _run_main_starting_fresh_daemon(
        tmp_path, socket_path, fake_connection_class, assert_socket_gone=False
    )

    assert code == 1
    assert 'error' in result
    assert 'exception' in result


def test_shutdown_with_socket_file_but_no_connection(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = listener
    process._socket_file_id = _socket_file_id(socket_path)
    process.connection = None

    process.shutdown()

    assert not os.path.exists(socket_path)
    assert listener.fileno() == -1


def test_shutdown_without_socket_does_not_unlink(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    socket_path.touch()

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = None
    process.connection = None

    process.shutdown()

    assert os.path.exists(socket_path)


def test_shutdown_does_not_unlink_socket_owned_by_another_daemon(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    old_listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    old_listener.bind(str(socket_path))
    old_listener.listen(1)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = old_listener
    process._socket_file_id = _socket_file_id(socket_path)
    fake_connection = _FakePluginConnection()
    fake_connection.socket_path = str(socket_path)
    process.connection = fake_connection

    os.remove(socket_path)
    new_listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    new_listener.bind(str(socket_path))
    new_listener.listen(1)

    try:
        process.shutdown()
    finally:
        new_listener.close()

    assert fake_connection.closed
    assert old_listener.fileno() == -1
    assert os.path.exists(socket_path)


def test_shutdown_closes_connection_when_socket_file_already_gone(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)
    socket_file_id = _socket_file_id(socket_path)
    os.remove(socket_path)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = listener
    process._socket_file_id = socket_file_id
    fake_connection = _FakePluginConnection()
    fake_connection.socket_path = str(socket_path)
    process.connection = fake_connection

    process.shutdown()

    assert fake_connection.closed
    assert listener.fileno() == -1


def test_shutdown_closes_connection_before_clearing_connection_state(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = listener
    process._socket_file_id = _socket_file_id(socket_path)
    fake_connection = _FakePluginConnection()
    fake_connection.socket_path = str(socket_path)
    fake_connection._connected = True
    fake_connection._socket_path = str(socket_path)
    process.connection = fake_connection

    process.shutdown()

    assert fake_connection.closed
    assert fake_connection.connected_at_close is True
    assert fake_connection.socket_path_at_close == str(socket_path)
    assert fake_connection._connected is False
    assert fake_connection._socket_path is None
    assert not os.path.exists(socket_path)
    assert listener.fileno() == -1


def test_shutdown_clears_connection_state_when_close_fails(tmp_path):
    socket_path = tmp_path / 'pc-sock'
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)

    process = stub.ConnectionProcess(None, None, str(socket_path), str(tmp_path))
    process.sock = listener
    process._socket_file_id = _socket_file_id(socket_path)
    fake_connection = _FakePluginConnection()
    fake_connection.socket_path = str(socket_path)
    fake_connection._connected = True
    fake_connection._socket_path = str(socket_path)
    fake_connection.close_error = RuntimeError('close failed')
    process.connection = fake_connection

    process.shutdown()

    assert fake_connection.closed
    assert fake_connection._connected is False
    assert fake_connection._socket_path is None
    assert not os.path.exists(socket_path)
    assert listener.fileno() == -1
