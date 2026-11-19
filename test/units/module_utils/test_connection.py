# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils import connection

import pytest


@pytest.mark.parametrize('method_name', ['set_options', 'set_options_ansible_connection_cli_stub'])
def test_set_options_credential_exposure(method_name):
    def send(data):
        return '{'

    c = connection.Connection(connection.__file__)
    c.send = send
    with pytest.raises(connection.ConnectionError) as excinfo:
        c._exec_jsonrpc(method_name, become_pass='password')

    assert 'password' not in str(excinfo.value)
