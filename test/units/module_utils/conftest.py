# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

import pytest

import ansible.module_utils.basic

from ansible.module_utils.testing import patch_module_args
from ..mock.module import module_env_mocker  # expose shared fixture in this part of the unit test tree

assert module_env_mocker is not None  # avoid unused imports


@pytest.fixture
def stdin(request):
    old_argv = sys.argv
    sys.argv = ['ansible_unittest']

    try:
        args = request.param.copy()
    except AttributeError:
        args = {}

    args.setdefault('_ansible_remote_tmp', '/tmp')
    args.setdefault('_ansible_keep_remote_files', False)
    args.setdefault('_ansible_tracebacks_for', [])

    with patch_module_args(args):
        yield

    sys.argv = old_argv


@pytest.fixture
def am(stdin, request):
    old_argv = sys.argv
    sys.argv = ['ansible_unittest']

    argspec = {}
    if hasattr(request, 'param'):
        if isinstance(request.param, dict):
            argspec = request.param

    am = ansible.module_utils.basic.AnsibleModule(
        argument_spec=argspec,
    )
    am._name = 'ansible_unittest'

    yield am

    sys.argv = old_argv
