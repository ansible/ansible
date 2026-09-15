# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from unittest.mock import MagicMock, call

from ansible.cli.scripts.ansible_connection_cli_stub import _ConnectionProcessRpc
from ansible.module_utils.connection import ConnectionError


def test_connection_process_rpc_synchronizes_connection_state_in_order():
    connection = MagicMock()
    connection.pop_messages.return_value = [('warning', 'queued warning')]
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub(
        options={'persistent_command_timeout': 42},
        play_context_data='serialized play context',
        task_uuid='task uuid',
    )

    assert connection.method_calls == [
        call.set_options(direct={'persistent_command_timeout': 42}),
        call.update_play_context('serialized play context'),
        call.set_check_prompt('task uuid'),
        call.pop_messages(),
    ]
    assert result == {
        'messages': [
            ('vvvv', 'found existing local domain socket, using it!'),
            ('warning', 'queued warning'),
        ],
        'socket_path': '/path/to/socket',
    }


def test_connection_process_rpc_skips_optional_connection_methods():
    class MinimalConnection:
        def __init__(self):
            self.options = None

        def set_options(self, *, direct):
            self.options = direct

        def pop_messages(self):
            return []

    connection = MinimalConnection()
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub({}, 'serialized play context', 'task uuid')

    assert connection.options == {}
    assert 'error' not in result


def test_connection_process_rpc_updates_context_without_check_prompt():
    class ContextOnlyConnection:
        def __init__(self):
            self.calls = []

        def set_options(self, *, direct):
            self.calls.append(('set_options', direct))

        def update_play_context(self, play_context_data):
            self.calls.append(('update_play_context', play_context_data))

        def pop_messages(self):
            self.calls.append(('pop_messages',))
            return [('warning', 'context-only warning')]

    connection = ContextOnlyConnection()
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub(
        options={'persistent_command_timeout': 42},
        play_context_data='serialized play context',
        task_uuid='task uuid',
    )

    assert connection.calls == [
        ('set_options', {'persistent_command_timeout': 42}),
        ('update_play_context', 'serialized play context'),
        ('pop_messages',),
    ]
    assert result == {
        'messages': [
            ('vvvv', 'found existing local domain socket, using it!'),
            ('warning', 'context-only warning'),
        ],
        'socket_path': '/path/to/socket',
    }


def test_connection_process_rpc_marshals_connection_errors_without_options():
    connection = MagicMock()
    connection.set_options.side_effect = ConnectionError('invalid response')
    connection.pop_messages.return_value = [('debug', 'potentially sensitive detail')]
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub(
        options={'password': 'secret'},
        play_context_data='serialized play context',
        task_uuid='task uuid',
    )

    assert result['error'] == 'Unable to decode JSON from response set_options. See the debug log for more information.'
    assert 'secret' not in result['exception']
    assert result['messages'] == [('vvvv', 'found existing local domain socket, using it!')]
    connection.update_play_context.assert_not_called()
    connection.set_check_prompt.assert_not_called()
    connection.pop_messages.assert_called_once_with()


def test_connection_process_rpc_redacts_non_connection_set_options_errors():
    secret = 'sentinel set_options secret'
    connection = MagicMock()
    connection.set_options.side_effect = ValueError(f'invalid password: {secret}')
    connection.pop_messages.return_value = [('debug', f'option processing failed: {secret}')]
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub(
        options={'password': secret},
        play_context_data='serialized play context',
        task_uuid='task uuid',
    )

    assert result['error'] == 'Unable to decode JSON from response set_options. See the debug log for more information.'
    assert secret not in repr(result)
    assert result['messages'] == [('vvvv', 'found existing local domain socket, using it!')]
    connection.update_play_context.assert_not_called()
    connection.set_check_prompt.assert_not_called()
    connection.pop_messages.assert_called_once_with()


def test_connection_process_rpc_marshals_context_update_errors():
    connection = MagicMock()
    connection.update_play_context.side_effect = RuntimeError('context update failed')
    connection.pop_messages.return_value = [('debug', 'queued message')]
    rpc = _ConnectionProcessRpc(connection, '/path/to/socket')

    result = rpc.set_options_ansible_connection_cli_stub({}, 'serialized play context', 'task uuid')

    assert result['error'] == 'context update failed'
    assert 'RuntimeError: context update failed' in result['exception']
    assert result['messages'][-1] == ('debug', 'queued message')
    connection.set_check_prompt.assert_not_called()
    connection.pop_messages.assert_called_once_with()
