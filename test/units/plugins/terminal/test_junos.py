# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Fran Fitzpatrick <francis.x.fitzpatrick@gmail.com> fxfitz
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from mock import call, MagicMock
import pytest

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.terminal import junos


@pytest.fixture
def junos_terminal():
    mock_connection = MagicMock()
    return junos.TerminalModule(mock_connection)


def test_on_open_shell_sets_terminal_parameters(junos_terminal):
    expected_calls = [
        call(b'set cli timestamp disable'),
        call(b'set cli screen-length 0'),
        call(b'set cli screen-width 1024'),
    ]
    junos_terminal._exec_cli_command = MagicMock()
    junos_terminal._get_prompt = MagicMock()

    junos_terminal._get_prompt.return_value = b'user@localhost >'
    junos_terminal.on_open_shell()
    junos_terminal._exec_cli_command.assert_has_calls(expected_calls)


def test_on_open_shell_enters_cli_if_root_prompt(junos_terminal):
    expected_calls = [
        call(b'cli'),
        call(b'set cli timestamp disable'),
        call(b'set cli screen-length 0'),
        call(b'set cli screen-width 1024'),
    ]
    junos_terminal._exec_cli_command = MagicMock()
    junos_terminal._get_prompt = MagicMock()

    junos_terminal._connection.get_prompt.return_value = b'root@localhost%'
    junos_terminal.on_open_shell()
    junos_terminal._exec_cli_command.assert_has_calls(expected_calls)


def test_on_open_shell_raises_problem_setting_terminal_config(junos_terminal):
    junos_terminal._connection.exec_command.side_effect = AnsibleConnectionFailure
    with pytest.raises(AnsibleConnectionFailure) as exc:
        junos_terminal.on_open_shell()

    assert 'unable to set terminal parameters' in str(exc.value)
