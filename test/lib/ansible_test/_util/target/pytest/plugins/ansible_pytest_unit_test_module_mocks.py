# -*- coding: utf-8 -*-

# Copyright (c) 2017–2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Pytest fixtures for mocking Ansible modules."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from io import BytesIO
import json
import sys

import pytest

import ansible.module_utils.basic
from ansible.module_utils.six import PY3, string_types
from ansible.module_utils.six.moves.collections_abc import MutableMapping
from ansible.module_utils.common.text.converters import to_bytes


@pytest.fixture
def patch_ansible_module(request, mocker):
    """Monkey-patch given Ansible module."""
    if isinstance(request.param, string_types):
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
        raise Exception('Malformed data to the patch_ansible_module pytest fixture')

    mocker.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args))


@pytest.fixture
def stdin(mocker, monkeypatch, request):
    """Patch and return stdin buffer with module args."""
    monkeypatch.setattr(ansible.module_utils.basic, '_ANSIBLE_ARGS', None)
    monkeypatch.setattr(sys, 'argv', ['ansible_unittest'])

    if isinstance(request.param, string_types):
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

    fake_stdin = BytesIO(to_bytes(args, errors='surrogate_or_strict'))
    if PY3:
        mocker.patch('ansible.module_utils.basic.sys.stdin', mocker.MagicMock())
        mocker.patch('ansible.module_utils.basic.sys.stdin.buffer', fake_stdin)
    else:
        mocker.patch('ansible.module_utils.basic.sys.stdin', fake_stdin)

    return fake_stdin


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
