# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Abhay Kadam <abhaykadam88@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

import pytest

from ansible.plugins.loader import lookup_loader


@pytest.mark.parametrize('env_var,exp_value', [
    ('foo', 'bar'),
    ('equation', 'a=b*100')
])
def test_env_var_value(monkeypatch, env_var, exp_value):
    original_environ_get = os.environ.get

    def environ_get(key: str, *args, **kwargs) -> str | None:
        if key == env_var:
            return exp_value

        return original_environ_get(key, *args, **kwargs)

    monkeypatch.setattr('os.environ.get', environ_get)

    env_lookup = lookup_loader.get('env')
    retval = env_lookup.run([env_var], None)
    assert retval == [exp_value]


@pytest.mark.parametrize('env_var,exp_value', [
    ('simple_var', 'alpha-β-gamma'),
    ('the_var', 'ãnˈsiβle')
])
def test_utf8_env_var_value(monkeypatch, env_var, exp_value):
    original_environ_get = os.environ.get

    def environ_get(key: str, *args, **kwargs) -> str | None:
        if key == env_var:
            return exp_value

        return original_environ_get(key, *args, **kwargs)

    monkeypatch.setattr('os.environ.get', environ_get)

    env_lookup = lookup_loader.get('env')
    retval = env_lookup.run([env_var], None)
    assert retval == [exp_value]
