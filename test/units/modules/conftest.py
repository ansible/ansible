# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing as t

import pytest

from ansible.module_utils.testing import patch_module_args

from ..mock.module import module_env_mocker  # expose shared fixture in this part of the unit test tree

assert module_env_mocker is not None  # avoid unused imports


@pytest.fixture
def patch_ansible_module(request):
    request.param = {'ANSIBLE_MODULE_ARGS': request.param}
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False

    args = json.dumps(request.param)

    with patch_module_args(args, 'legacy'):
        yield


@pytest.fixture
def set_module_args():
    ctx: t.ContextManager | None = None

    def set_module_args(args):
        nonlocal ctx

        args['_ansible_remote_tmp'] = '/tmp'
        args['_ansible_keep_remote_files'] = False

        args = json.dumps({'ANSIBLE_MODULE_ARGS': args})

        ctx = patch_module_args(args, 'legacy')
        ctx.__enter__()

    try:
        yield set_module_args
    finally:
        if ctx:
            ctx.__exit__(None, None, None)
