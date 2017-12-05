# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

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
    if isinstance(request.param, string_types):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if 'ANSIBLE_MODULE_ARGS' not in request.param:
            request.param = {'ANSIBLE_MODULE_ARGS': request.param}
        args = json.dumps(request.param)
    else:
        raise Exception('Malformed data to the stdin pytest fixture')

    real_stdin = sys.stdin
    fake_stdin = BytesIO(to_bytes(args, errors='surrogate_or_strict'))
    if PY3:
        sys.stdin = mocker.MagicMock()
        sys.stdin.buffer = fake_stdin
    else:
        sys.stdin = fake_stdin

    yield fake_stdin

    sys.stdin = real_stdin


@pytest.fixture
def am(stdin, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ['ansible_unittest']

    am = ansible.module_utils.basic.AnsibleModule(
        argument_spec=dict(),
    )
    am._name = 'ansible_unittest'

    yield am

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv


@pytest.mark.parametrize('stdin', [{}], indirect=True)
def test_warn(am, capfd):

    am.warn('warning1')

    with pytest.raises(SystemExit):
        am.exit_json(warnings=['warning2'])
    out, err = capfd.readouterr()
    assert json.loads(out)['warnings'] == ['warning1', 'warning2']


@pytest.mark.parametrize('stdin', [{}], indirect=True)
def test_deprecate(am, capfd):
    am.deprecate('deprecation1')
    am.deprecate('deprecation2', '2.3')

    with pytest.raises(SystemExit):
        am.exit_json(deprecations=['deprecation3', ('deprecation4', '2.4')])

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'deprecation1', u'version': None},
        {u'msg': u'deprecation2', u'version': '2.3'},
        {u'msg': u'deprecation3', u'version': None},
        {u'msg': u'deprecation4', u'version': '2.4'},
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=True)
def test_deprecate_without_list(am, capfd):
    with pytest.raises(SystemExit):
        am.exit_json(deprecations='Simple deprecation warning')

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'Simple deprecation warning', u'version': None},
    ]
