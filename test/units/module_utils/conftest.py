# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import sys
from collections import MutableMapping
from io import BytesIO

import pytest

import ansible.module_utils.basic
from ansible.module_utils.six import PY3, string_types
from ansible.module_utils._text import to_bytes


@pytest.fixture
def stdin(mocker, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ['ansible_unittest']

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

    yield fake_stdin

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv


@pytest.fixture
def am(stdin, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
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

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv
