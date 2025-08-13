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

import sys
from io import StringIO
import pytest
import typing as t

from ansible.module_utils import _internal
from ansible.plugins.connection import paramiko_ssh as paramiko_ssh_module
from ansible.plugins.loader import connection_loader
from ansible.playbook.play_context import PlayContext

from units.test_utils.controller.display import emits_warnings


@pytest.fixture
def play_context():
    play_context = PlayContext()
    play_context.prompt = (
        '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
    )

    return play_context


@pytest.fixture()
def in_stream():
    return StringIO()


def test_paramiko_connection_module(play_context, in_stream):
    assert isinstance(
        connection_loader.get('paramiko_ssh', play_context, in_stream),
        paramiko_ssh_module.Connection)


def test_paramiko_connect(play_context, in_stream, mocker):
    paramiko_ssh = connection_loader.get('paramiko_ssh', play_context, in_stream)
    mocker.patch.object(paramiko_ssh, '_connect_uncached')
    connection = paramiko_ssh._connect()

    assert isinstance(connection, paramiko_ssh_module.Connection)
    assert connection._connected is True


def test_deprecation_warning_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensures deprecation warnings are generated for external paramiko imports."""
    assert _internal.is_controller

    sentinel: t.Any = object()

    monkeypatch.delitem(sys.modules, 'ansible')
    monkeypatch.delitem(sys.modules, 'ansible.module_utils')
    monkeypatch.delitem(sys.modules, 'ansible.module_utils.compat')
    monkeypatch.delitem(sys.modules, 'ansible.module_utils.compat.paramiko')
    monkeypatch.setitem(sys.modules, 'paramiko', sentinel)

    # ensure direct access to `_` prefixed attrs does not warn
    with emits_warnings(deprecation_pattern=[], warning_pattern=[]):
        from ansible.module_utils.compat import paramiko
        assert paramiko._paramiko is sentinel
        assert isinstance(paramiko._PARAMIKO_IMPORT_ERR, (Exception, type(None)))

    with emits_warnings(deprecation_pattern=["The 'paramiko' compat import is deprecated", "The 'PARAMIKO_IMPORT_ERR' compat import is deprecated"]):
        from ansible.module_utils.compat import paramiko
        assert paramiko.paramiko is sentinel
        assert isinstance(paramiko.PARAMIKO_IMPORT_ERR, (Exception, type(None)))
