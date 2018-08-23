# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from ansible.errors import AnsibleParserError
from ansible.playbook.become import Become
from ansible.module_utils._text import to_native

import pytest


class InString(str):
    def __eq__(self, other):
        return self in other


@pytest.mark.parametrize("ds", [
    {},
    {'become': True},
    {'become_user': 'root'},
    {'sudo': True},
    {'sudo_user': 'root'},
    {'su': True},
    {'su_user': 'root'}
])
def test_detect_privilege_escalation_conflict_valid(ds):
    become = Become()
    become._detect_privilege_escalation_conflict(ds)


@pytest.mark.parametrize("ds,message", [
    ({'become': True, 'sudo': True}, re.compile('"become".*"sudo"')),
    ({'become': True, 'su': True}, re.compile('"become".*"su"')),
    ({'sudo': True, 'su': True}, re.compile('"sudo".*"su"')),
    ({'become_user': 'root', 'sudo': True}, re.compile('"become".*"sudo"')),
    ({'sudo_user': 'root', 'su': True}, re.compile('"sudo".*"su"')),
])
def test_detect_privilege_escalation_conflict_invalid(ds, message):
    become = Become()
    with pytest.raises(AnsibleParserError) as excinfo:
        become._detect_privilege_escalation_conflict(ds)
    assert message.search(excinfo.value.message) is not None


def test_preprocess_data_become(mocker):
    display_mock = mocker.patch('ansible.playbook.become.display')

    become = Become()
    ds = {}
    assert become._preprocess_data_become(ds) == {}

    display_mock.reset_mock()
    ds = {'sudo': True}
    out = become._preprocess_data_become(ds)
    assert 'sudo' not in out
    assert out.get('become_method') == 'sudo'
    display_mock.deprecated.assert_called_once_with(
        "Instead of sudo/sudo_user, use become/become_user and make sure become_method is 'sudo' (default)",
        '2.9'
    )

    ds = {'sudo_user': 'root'}
    out = become._preprocess_data_become(ds)
    assert 'sudo_user' not in out
    assert out.get('become_user') == 'root'

    ds = {'sudo': True, 'sudo_user': 'root'}
    out = become._preprocess_data_become(ds)
    assert 'sudo' not in out
    assert 'sudo_user' not in out
    assert out.get('become_method') == 'sudo'
    assert out.get('become_user') == 'root'

    display_mock.reset_mock()
    ds = {'su': True}
    out = become._preprocess_data_become(ds)
    assert 'su' not in out
    assert out.get('become_method') == 'su'
    display_mock.deprecated.assert_called_once_with(
        "Instead of su/su_user, use become/become_user and set become_method to 'su' (default is sudo)",
        '2.9'
    )
    display_mock.reset_mock()

    ds = {'su_user': 'root'}
    out = become._preprocess_data_become(ds)
    assert 'su_user' not in out
    assert out.get('become_user') == 'root'

    ds = {'su': True, 'su_user': 'root'}
    out = become._preprocess_data_become(ds)
    assert 'su' not in out
    assert 'su_user' not in out
    assert out.get('become_method') == 'su'
    assert out.get('become_user') == 'root'
