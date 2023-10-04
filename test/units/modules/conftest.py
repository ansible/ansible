# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json

import pytest

from ansible.module_utils.common.text.converters import to_bytes


@pytest.fixture
def patch_ansible_module(request, mocker):
    request.param = {'ANSIBLE_MODULE_ARGS': request.param}
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
    request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False

    args = json.dumps(request.param)

    mocker.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args))
