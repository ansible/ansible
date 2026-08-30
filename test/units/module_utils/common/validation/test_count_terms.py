# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.validation import count_terms


@pytest.fixture
def params():
    return {
        'name': 'bob',
        'dest': '/etc/hosts',
        'state': 'present',
        'value': 5,
    }


def test_count_terms(params):
    check = set(('name', 'dest'))
    assert count_terms(check, params) == 2


def test_count_terms_str_input(params):
    check = 'name'
    assert count_terms(check, params) == 1


def test_count_terms_tuple_input(params):
    check = ('name', 'dest')
    assert count_terms(check, params) == 2


def test_count_terms_list_input(params):
    check = ['name', 'dest']
    assert count_terms(check, params) == 2


def test_count_terms_none_value():
    params = {'name': 'bob', 'dest': None, 'other': None}
    assert count_terms(['name', 'dest'], params) == 1
    assert count_terms(['dest', 'other'], params) == 0
    assert count_terms('dest', params) == 0

