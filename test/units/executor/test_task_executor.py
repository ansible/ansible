# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json
import pickle
import subprocess
import sys
from contextlib import contextmanager, nullcontext
from unittest.mock import MagicMock, call

import pytest

from ansible.errors import AnsibleError
from ansible.executor import task_executor
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.connection import ConnectionError


@pytest.fixture
def play_context():
    value = MagicMock()
    value.remote_addr = 'example.invalid'
    value.dump_attrs.return_value = {'remote_addr': 'example.invalid', 'password': 'surrogate\udcff'}
    return value


@pytest.fixture(autouse=True)
def connection_lock(mocker):
    return mocker.patch.object(task_executor, '_persistent_connection_lock', side_effect=lambda lock_path: nullcontext())


def test_start_connection_uses_existing_socket_without_subprocess(mocker, play_context, connection_lock):
    options = {'persistent_command_timeout': 42}
    connection = mocker.patch.object(task_executor, 'Connection').return_value
    connection.set_options_ansible_connection_cli_stub.return_value = {
        'messages': [],
        'socket_path': '/path/to/socket',
    }
    get_socket_path = mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/path/to/socket')
    mocker.patch.object(task_executor.os.path, 'exists', return_value=True)
    cli_stub = mocker.patch.object(task_executor, '_start_connection_cli_stub')

    result = task_executor.start_connection(play_context, options, 'task uuid')

    assert result == '/path/to/socket'
    get_socket_path.assert_called_once_with(play_context, task_executor.os.getppid())
    connection_lock.assert_called_once_with('/path/to/.ansible_pc_lock_socket')
    connection.set_options_ansible_connection_cli_stub.assert_called_once_with(
        options=options,
        play_context_data=to_text(pickle.dumps(play_context.dump_attrs())),
        task_uuid='task uuid',
    )
    cli_stub.assert_not_called()


def test_start_connection_uses_subprocess_without_existing_socket(mocker, play_context):
    mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/missing/socket')
    mocker.patch.object(task_executor.os.path, 'exists', return_value=False)
    cli_stub = mocker.patch.object(
        task_executor,
        '_start_connection_cli_stub',
        return_value={'messages': [], 'socket_path': '/new/socket'},
    )

    result = task_executor.start_connection(play_context, {}, 'task uuid')

    assert result == '/new/socket'
    cli_stub.assert_called_once_with(play_context, {}, 'task uuid')


@pytest.mark.parametrize(
    ('error', 'socket_exists'),
    [
        (ConnectionError('method not found', code=-32601), [True, True]),
        (ConnectionError('socket disappeared'), [True, True, False]),
    ],
)
def test_start_connection_falls_back_for_unsupported_or_disappeared_socket(mocker, play_context, error, socket_exists):
    connection = mocker.patch.object(task_executor, 'Connection').return_value
    connection.set_options_ansible_connection_cli_stub.side_effect = error
    mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/old/socket')
    mocker.patch.object(task_executor.os.path, 'exists', side_effect=socket_exists)
    cli_stub = mocker.patch.object(
        task_executor,
        '_start_connection_cli_stub',
        return_value={'messages': [], 'socket_path': '/new/socket'},
    )

    result = task_executor.start_connection(play_context, {}, 'task uuid')

    assert result == '/new/socket'
    cli_stub.assert_called_once_with(play_context, {}, 'task uuid')


def test_start_connection_does_not_retry_other_existing_socket_errors(mocker, play_context):
    connection = mocker.patch.object(task_executor, 'Connection').return_value
    connection.set_options_ansible_connection_cli_stub.side_effect = ConnectionError('connection refused')
    mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/stale/socket')
    mocker.patch.object(task_executor.os.path, 'exists', return_value=True)
    cli_stub = mocker.patch.object(task_executor, '_start_connection_cli_stub')

    with pytest.raises(AnsibleError, match='connection refused'):
        task_executor.start_connection(play_context, {}, 'task uuid')

    cli_stub.assert_not_called()


def test_start_connection_does_not_retry_daemon_operation_errors(mocker, play_context):
    connection = mocker.patch.object(task_executor, 'Connection').return_value
    connection.set_options_ansible_connection_cli_stub.return_value = {
        'error': 'context update failed',
        'exception': 'daemon traceback',
        'messages': [],
        'socket_path': '/path/to/socket',
    }
    mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/path/to/socket')
    mocker.patch.object(task_executor.os.path, 'exists', return_value=True)
    cli_stub = mocker.patch.object(task_executor, '_start_connection_cli_stub')

    with pytest.raises(AnsibleError, match='context update failed'):
        task_executor.start_connection(play_context, {}, 'task uuid')

    cli_stub.assert_not_called()


def test_start_connection_waits_for_creation_lock_before_using_socket(mocker, play_context, connection_lock):
    events = []
    socket_checks = iter([False, True])

    def exists(path):
        if path == '/path/to/socket':
            events.append('socket-exists')
            return next(socket_checks)
        if path == '/path/to/lock':
            events.append('lock-exists')
            return True
        raise AssertionError(f'unexpected path: {path}')

    @contextmanager
    def acquire_lock(lock_path):
        assert lock_path == '/path/to/lock'
        events.append('lock-enter')
        try:
            yield
        finally:
            events.append('lock-exit')

    connection_lock.side_effect = acquire_lock
    mocker.patch.object(task_executor, '_get_persistent_connection_socket_path', return_value='/path/to/socket')
    mocker.patch.object(task_executor, '_get_persistent_connection_lock_path', return_value='/path/to/lock')
    mocker.patch.object(task_executor.os.path, 'exists', side_effect=exists)
    connection = mocker.patch.object(task_executor, 'Connection').return_value

    def synchronize(**kwargs):
        events.append('rpc')
        return {'messages': [], 'socket_path': '/path/to/socket'}

    connection.set_options_ansible_connection_cli_stub.side_effect = synchronize
    cli_stub = mocker.patch.object(task_executor, '_start_connection_cli_stub')

    result = task_executor.start_connection(play_context, {}, 'task uuid')

    assert result == '/path/to/socket'
    assert events == ['socket-exists', 'lock-exists', 'lock-enter', 'socket-exists', 'rpc', 'lock-exit']
    cli_stub.assert_not_called()


def test_start_connection_cli_stub_uses_configured_path(mocker, play_context, collection_loader):
    process = MagicMock()
    process.returncode = 0
    process.communicate.return_value = (json.dumps({'messages': [], 'socket_path': '/new/socket'}).encode(), b'')
    popen = mocker.patch.object(task_executor.subprocess, 'Popen', return_value=process)
    write_to_stream = mocker.patch.object(task_executor, 'write_to_stream')
    mocker.patch.object(task_executor.C.config, 'get_config_value', return_value='/custom/connection-helper')

    result = task_executor._start_connection_cli_stub(play_context, {'timeout': 42}, 'task uuid')

    assert result == {'messages': [], 'socket_path': '/new/socket'}
    assert popen.call_args.args[0] == [sys.executable, '/custom/connection-helper', to_text(task_executor.os.getppid()), 'task uuid']
    assert popen.call_args.kwargs['stdin'] is subprocess.PIPE
    assert popen.call_args.kwargs['stdout'] is subprocess.PIPE
    assert popen.call_args.kwargs['stderr'] is subprocess.PIPE
    assert write_to_stream.call_args_list == [
        call(process.stdin, {'timeout': 42}),
        call(process.stdin, play_context.dump_attrs()),
    ]


@pytest.mark.parametrize('level', ['debug', 'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv'])
def test_handle_connection_result_dispatches_host_messages(mocker, play_context, level):
    display = mocker.patch.object(task_executor, 'display')

    result = task_executor._handle_connection_result(
        play_context,
        {'messages': [(level, 'message')], 'socket_path': '/path/to/socket'},
    )

    assert result == '/path/to/socket'
    getattr(display, level).assert_called_once_with('message', host='example.invalid')


def test_handle_connection_result_dispatches_other_messages(mocker, play_context):
    display = mocker.patch.object(task_executor, 'display', autospec=True)

    task_executor._handle_connection_result(
        play_context,
        {
            'messages': [
                ('log', 'log message'),
                ('warning', 'warning message'),
                ('unknown', 'unknown message'),
            ],
            'socket_path': '/path/to/socket',
        },
    )

    display.display.assert_called_once_with('log message', log_only=True)
    display.warning.assert_called_once_with('warning message')
    display.vvvv.assert_called_once_with('unknown message', host='example.invalid')
