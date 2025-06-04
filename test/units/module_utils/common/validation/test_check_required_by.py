# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

import pytest

from ansible.module_utils.common.validation import check_required_by


@pytest.fixture
def path_arguments_terms():
    return {
        "path": ["mode", "owner"],
    }


def test_check_required_by():
    assert check_required_by({}, {}) == {}


def test_check_required_by_missing():
    arguments_terms = {
        "force": "force_reason",
    }
    params = {"force": True}
    expected = "missing parameter(s) required by 'force': force_reason"
    with pytest.raises(TypeError, match=re.escape(expected)):
        check_required_by(arguments_terms, params)


def test_check_required_by_multiple(path_arguments_terms):
    params = {
        "path": "/foo/bar",
    }
    expected = "missing parameter(s) required by 'path': mode, owner"

    with pytest.raises(TypeError, match=re.escape(expected)):
        check_required_by(path_arguments_terms, params)


def test_check_required_by_single(path_arguments_terms):
    params = {"path": "/foo/bar", "mode": "0700"}
    expected = "missing parameter(s) required by 'path': owner"

    with pytest.raises(TypeError, match=re.escape(expected)):
        check_required_by(path_arguments_terms, params)


def test_check_required_by_missing_none(path_arguments_terms):
    params = {
        "path": "/foo/bar",
        "mode": "0700",
        "owner": "root",
    }
    assert check_required_by(path_arguments_terms, params) == {}


def test_check_required_by_options_context(path_arguments_terms):
    params = {"path": "/foo/bar", "mode": "0700"}

    options_context = ["foo_context"]

    expected = "missing parameter(s) required by 'path': owner found in foo_context"

    with pytest.raises(TypeError, match=re.escape(expected)):
        check_required_by(path_arguments_terms, params, options_context)


def test_check_required_by_missing_multiple_options_context(path_arguments_terms):
    params = {
        "path": "/foo/bar",
    }
    options_context = ["foo_context"]

    expected = (
        "missing parameter(s) required by 'path': mode, owner found in foo_context"
    )

    with pytest.raises(TypeError, match=re.escape(expected)):
        check_required_by(path_arguments_terms, params, options_context)
