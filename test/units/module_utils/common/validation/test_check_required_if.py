# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_required_if


def test_check_required_if():
    arguments_terms = {}
    params = {}
    assert check_required_if(arguments_terms, params) == []


def test_check_required_if_missing():
    arguments_terms = [["state", "present", ("path",)]]
    params = {"state": "present"}
    expected = "state is present but all of the following are missing: path"

    with pytest.raises(TypeError) as e:
        check_required_if(arguments_terms, params)

    assert to_native(e.value) == expected


def test_check_required_if_missing_required():
    arguments_terms = [["state", "present", ("path", "owner"), True]]
    params = {"state": "present"}
    expected = "state is present but any of the following are missing: path, owner"

    with pytest.raises(TypeError) as e:
        check_required_if(arguments_terms, params)

    assert to_native(e.value) == expected


def test_check_required_if_missing_multiple():
    arguments_terms = [["state", "present", ("path", "owner")]]
    params = {
        "state": "present",
    }
    expected = "state is present but all of the following are missing: path, owner"

    with pytest.raises(TypeError) as e:
        check_required_if(arguments_terms, params)

    assert to_native(e.value) == expected


def test_check_required_if_missing_multiple_with_context():
    arguments_terms = [["state", "present", ("path", "owner")]]
    params = {
        "state": "present",
    }
    options_context = ["foo_context"]
    expected = "state is present but all of the following are missing: path, owner found in foo_context"

    with pytest.raises(TypeError) as e:
        check_required_if(arguments_terms, params, options_context)

    assert to_native(e.value) == expected


def test_check_required_if_multiple():
    arguments_terms = [["state", "present", ("path", "owner")]]
    params = {
        "state": "present",
        "path": "/foo",
        "owner": "root",
    }
    options_context = ["foo_context"]
    assert check_required_if(arguments_terms, params) == []
    assert check_required_if(arguments_terms, params, options_context) == []
