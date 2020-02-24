# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Pytest fixtures for mocking Ansible modules."""

from __future__ import annotations

import json
import sys
from io import BytesIO

import pytest

import ansible.module_utils.basic
from ansible.module_utils.common.text.converters import to_bytes
from collections.abc import MutableMapping


@pytest.fixture
def patch_ansible_module(monkeypatch, request):
    """Monkey-patch given Ansible module."""
    request.param = {'ANSIBLE_MODULE_ARGS': request.param}
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False

    args = json.dumps(request.param)

    monkeypatch.setattr(
        ansible.module_utils.basic, '_ANSIBLE_ARGS',
        to_bytes(args),
    )


@pytest.fixture
def stdin(mocker, monkeypatch, request):
    """Patch and return stdin buffer with module args."""
    monkeypatch.setattr(ansible.module_utils.basic, '_ANSIBLE_ARGS', None)
    monkeypatch.setattr(sys, 'argv', ['ansible_unittest'])

    if isinstance(request.param, str):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if 'ANSIBLE_MODULE_ARGS' not in request.param:
            request.param = {'ANSIBLE_MODULE_ARGS': request.param}
        if '_ansible_remote_tmp' not in request.param['ANSIBLE_MODULE_ARGS']:
            request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
        if '_ansible_keep_remote_files' not in request.param['ANSIBLE_MODULE_ARGS']:
            request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False
        args = json.dumps(request.param)
    else:
        raise Exception('Malformed data to the stdin pytest fixture')

    fake_stdin_buffer = BytesIO(to_bytes(args, errors='surrogate_or_strict'))

    monkeypatch.setattr(
        ansible.module_utils.basic.sys, 'stdin',
        mocker.MagicMock(),
    )
    monkeypatch.setattr(
        ansible.module_utils.basic.sys.stdin, 'buffer',
        fake_stdin_buffer,
    )

    return fake_stdin_buffer


# pylint: disable=invalid-name,redefined-outer-name,unused-argument
@pytest.fixture
def am(stdin, request):
    """Return a patched Ansible module instance."""
    argspec = {}
    if isinstance(getattr(request, 'param', None), dict):
        argspec = request.param

    ans_mod = ansible.module_utils.basic.AnsibleModule(
        argument_spec=argspec,
    )
    ans_mod._name = 'ansible_unittest'  # pylint: disable=protected-access

    return ans_mod
