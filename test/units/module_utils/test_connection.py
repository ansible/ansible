# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils import connection

import pytest


def test_set_options_credential_exposure():
    def send(data):
        return '{'

    c = connection.Connection(connection.__file__)
    c.send = send
    with pytest.raises(connection.ConnectionError) as excinfo:
        c._exec_jsonrpc('set_options', become_pass='password')

    assert 'password' not in str(excinfo.value)
