# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_required_one_of


@pytest.fixture
def arguments_terms():
    return [["path", "owner"]]


def test_check_required_one_of():
    assert check_required_one_of([], {}) == []


@pytest.mark.parametrize("params", [
    {"state": "present"},
    {"path": None},
    {"owner": None},
    {"path": None, "owner": None},
])
def test_check_required_one_of_missing(arguments_terms: list[list[str]], params: dict[str, object]) -> None:
    expected = "one of the following is required: path, owner"
    original_params = params.copy()

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params)

    assert to_native(e.value) == expected
    assert params == original_params


@pytest.mark.parametrize("value", ["/foo", False, 0, "", [], {}])
def test_check_required_one_of_provided(arguments_terms: list[list[str]], value: object) -> None:
    params = {"state": "present", "path": value, "owner": None}
    original_params = params.copy()
    assert check_required_one_of(arguments_terms, params) == []
    assert params == original_params


@pytest.mark.parametrize("params", [
    {"state": "present"},
    {"path": None, "owner": None},
])
def test_check_required_one_of_context(arguments_terms: list[list[str]], params: dict[str, object]) -> None:
    expected = "one of the following is required: path, owner found in foo_context"
    option_context = ["foo_context"]

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params, option_context)

    assert to_native(e.value) == expected


def test_check_required_one_of_module_defaults() -> None:
    validator = ArgumentSpecValidator({"server": {"type": "str"}, "datacenter": {"type": "str"}})
    result = validator.validate({})
    assert result.error_messages == []
    assert result.validated_parameters == {"server": None, "datacenter": None}

    with pytest.raises(TypeError, match="^one of the following is required: server, datacenter$"):
        check_required_one_of([["server", "datacenter"]], result.validated_parameters)
