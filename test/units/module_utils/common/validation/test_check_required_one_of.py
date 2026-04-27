# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_required_one_of


@pytest.fixture
def arguments_terms():
    return [["path", "owner"]]


def test_check_required_one_of():
    assert check_required_one_of([], {}) == []


def test_check_required_one_of_missing(arguments_terms):
    params = {"state": "present"}
    expected = "one of the following is required: path, owner"

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params)

    assert to_native(e.value) == expected


def test_check_required_one_of_provided(arguments_terms):
    params = {"state": "present", "path": "/foo"}
    assert check_required_one_of(arguments_terms, params) == []


def test_check_required_one_of_context(arguments_terms):
    params = {"state": "present"}
    expected = "one of the following is required: path, owner found in foo_context"
    option_context = ["foo_context"]

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params, option_context)

    assert to_native(e.value) == expected
