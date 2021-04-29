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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from io import StringIO
import pytest

from ansible.plugins.connection import paramiko_ssh
from ansible.playbook.play_context import PlayContext


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
        paramiko_ssh.Connection(play_context, in_stream),
        paramiko_ssh.Connection)


def test_paramiko_connect(play_context, in_stream, mocker):
    mocker.patch.object(paramiko_ssh.Connection, '_connect_uncached')
    connection = paramiko_ssh.Connection(play_context, in_stream)._connect()

    assert isinstance(connection, paramiko_ssh.Connection)
    assert connection._connected is True
