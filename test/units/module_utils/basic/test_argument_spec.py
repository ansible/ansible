# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division)
__metaclass__ = type

import json

import pytest

from ansible.compat.tests.mock import MagicMock
from ansible.module_utils import basic


MOCK_VALIDATOR_SUCCESS = MagicMock(return_value=42)
MOCK_VALIDATOR_FAIL = MagicMock(side_effect=TypeError("bad conversion"))
# Data is argspec, argument, expected
VALID_SPECS = (
    ({'arg': {'type': int}}, {'arg': 42}, 42),
    ({'arg': {'type': int}}, {'arg': '42'}, 42),
    ({'arg': {'type': MOCK_VALIDATOR_SUCCESS}}, {'arg': 42}, 42),
)

INVALID_SPECS = (
    ({'arg': {'type': int}}, {'arg': "bad"}, "invalid literal for int() with base 10: 'bad'"),
    ({'arg': {'type': MOCK_VALIDATOR_FAIL}}, {'arg': "bad"}, "bad conversion"),
)


@pytest.mark.parametrize('argspec, expected, am, stdin', [(s[0], s[2], s[0], s[1]) for s in VALID_SPECS],
                         indirect=['am', 'stdin'])
def test_validator_success(am, mocker, argspec, expected):

    type_ = argspec['arg']['type']
    if isinstance(type_, MagicMock):
        assert type_.called
    else:
        assert isinstance(am.params['arg'], type_)
    assert am.params['arg'] == expected


@pytest.mark.parametrize('argspec, expected, stdin', [(s[0], s[2], s[1]) for s in INVALID_SPECS],
                         indirect=['stdin'])
def test_validator_fail(stdin, capfd, argspec, expected):
    with pytest.raises(SystemExit) as ecm:
        m = basic.AnsibleModule(argument_spec=argspec)

    out, err = capfd.readouterr()
    assert not err
    assert expected in json.loads(out)['msg']
    assert json.loads(out)['failed']
