# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

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


def test_count_terms_bad_input(params):
    check = ('name', 'dest')

    with pytest.raises(AttributeError):
        assert count_terms(check, params) == 2
