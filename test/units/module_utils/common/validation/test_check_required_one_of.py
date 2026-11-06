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


@pytest.fixture
def argument_spec() -> dict[str, dict[str, object]]:
    return {"path": {"type": "raw"}, "owner": {"type": "raw"}}


def test_check_required_one_of():
    assert check_required_one_of([], {}) == []


@pytest.mark.parametrize("params", [
    {"state": "present"},
    {"path": None},
    {"owner": None},
    {"path": None, "owner": None},
])
def test_check_required_one_of_missing(
    arguments_terms: list[list[str]], params: dict[str, object], argument_spec: dict[str, dict[str, object]],
) -> None:
    expected = "one of the following is required: path, owner"
    original_params = params.copy()

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params, argument_spec=argument_spec)

    assert to_native(e.value) == expected
    assert params == original_params


@pytest.mark.parametrize("value", ["/foo", False, 0, "", [], {}])
@pytest.mark.parametrize('with_spec', [False, True])
def test_check_required_one_of_provided(
    arguments_terms: list[list[str]], value: object, argument_spec: dict[str, dict[str, object]], with_spec: bool,
) -> None:
    params = {"state": "present", "path": value, "owner": None}
    original_params = params.copy()
    assert check_required_one_of(arguments_terms, params, argument_spec=argument_spec if with_spec else None) == []
    assert params == original_params


@pytest.mark.parametrize("params", [
    {"state": "present"},
    {"path": None, "owner": None},
])
def test_check_required_one_of_context(
    arguments_terms: list[list[str]], params: dict[str, object], argument_spec: dict[str, dict[str, object]],
) -> None:
    expected = "one of the following is required: path, owner found in foo_context"
    option_context = ["foo_context"]

    with pytest.raises(TypeError) as e:
        check_required_one_of(arguments_terms, params, option_context, argument_spec=argument_spec)

    assert to_native(e.value) == expected


def test_check_required_one_of_module_defaults() -> None:
    validator = ArgumentSpecValidator({"server": {"type": "str"}, "datacenter": {"type": "str"}})
    result = validator.validate({})
    assert result.error_messages == []
    assert result.validated_parameters == {"server": None, "datacenter": None}

    with pytest.raises(TypeError, match="^one of the following is required: server, datacenter$"):
        check_required_one_of([["server", "datacenter"]], result.validated_parameters, argument_spec=validator.argument_spec)


@pytest.mark.parametrize('params', [{"path": None}, {"owner": None}, {"path": None, "owner": None}])
def test_check_required_one_of_without_spec(arguments_terms: list[list[str]], params: dict[str, object]) -> None:
    assert check_required_one_of(arguments_terms, params) == []


@pytest.mark.parametrize('option_spec', [
    {'default': None},
    {'default': False},
    {'default': 0},
    {'default': ''},
    {'default': []},
    {'default': {}},
    {'default': '/foo'},
    {'choices': [None, '/foo']},
    {'choices': (None, '/foo')},
    {'choices': frozenset([None, '/foo'])},
])
def test_check_required_one_of_allowed_null(arguments_terms: list[list[str]], option_spec: dict[str, object]) -> None:
    params = {"path": None, "owner": None}
    original_params = params.copy()
    argument_spec = {'path': option_spec, 'owner': {}}

    assert check_required_one_of(arguments_terms, params, argument_spec=argument_spec) == []
    assert params == original_params


@pytest.mark.parametrize('option_spec', [{}, {'choices': None}, {'choices': []}, {'choices': ['/foo']}])
def test_check_required_one_of_null_sentinel(arguments_terms: list[list[str]], option_spec: dict[str, object]) -> None:
    with pytest.raises(TypeError, match='^one of the following is required: path, owner$'):
        check_required_one_of(arguments_terms, {'path': None}, argument_spec={'path': option_spec})


@pytest.mark.parametrize('option_spec', [{'default': None}, {'default': '/foo'}, {'choices': [None]}])
def test_check_required_one_of_spec_without_parameters(arguments_terms: list[list[str]], option_spec: dict[str, object]) -> None:
    with pytest.raises(TypeError, match='^one of the following is required: path, owner$'):
        check_required_one_of(arguments_terms, {}, argument_spec={'path': option_spec})
