# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from collections import MutableMapping

import pytest

from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes


@pytest.fixture
def patch_ansible_module(request, mocker):
    if isinstance(request.param, string_types):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if 'ANSIBLE_MODULE_ARGS' not in request.param:
            request.param = {'ANSIBLE_MODULE_ARGS': request.param}
        args = json.dumps(request.param)
    else:
        raise Exception('Malformed data to the patch_ansible_module pytest fixture')

    mocker.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args))
