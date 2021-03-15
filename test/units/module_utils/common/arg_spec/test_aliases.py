# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.errors import AnsibleValidationError, AnsibleValidationErrorMultiple
from ansible.module_utils.common.arg_spec import ArgumentSpecValidator, ValidationResult
from ansible.module_utils.common.warnings import get_deprecation_messages, get_warning_messages

# id, argument spec, parameters, expected parameters, deprecation, warning
ALIAS_TEST_CASES = [
    (
        "alias",
        {'path': {'aliases': ['dir', 'directory']}},
        {'dir': '/tmp'},
        {
            'dir': '/tmp',
            'path': '/tmp',
        },
        "",
        "",
    ),
    (
        "alias-duplicate-warning",
        {'path': {'aliases': ['dir', 'directory']}},
        {
            'dir': '/tmp',
            'directory': '/tmp',
        },
        {
            'dir': '/tmp',
            'directory': '/tmp',
            'path': '/tmp',
        },
        "",
        "Both option path and its alias directory are set",
    ),
    (
        "deprecated-alias",
        {
            'path': {
                'aliases': ['not_yo_path'],
                'deprecated_aliases': [
                    {
                        'name': 'not_yo_path',
                        'version': '1.7',
                    }
                ]
            }
        },
        {'not_yo_path': '/tmp'},
        {
            'path': '/tmp',
            'not_yo_path': '/tmp',
        },
        "Alias 'not_yo_path' is deprecated.",
        "",
    )
]


# id, argument spec, parameters, expected parameters, error
ALIAS_TEST_CASES_INVALID = [
    (
        "alias-invalid",
        {'path': {'aliases': 'bad'}},
        {},
        {'path': None},
        "internal error: aliases must be a list or tuple",
    ),
    (
        # This isn't related to aliases, but it exists in the alias handling code
        "default-and-required",
        {'name': {'default': 'ray', 'required': True}},
        {},
        {'name': 'ray'},
        "internal error: required and default are mutually exclusive for name",
    ),
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected', 'deprecation', 'warning'),
    ((i[1:]) for i in ALIAS_TEST_CASES),
    ids=[i[0] for i in ALIAS_TEST_CASES]
)
def test_aliases(arg_spec, parameters, expected, deprecation, warning):
    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.validated_parameters == expected
    assert result.error_messages == []

    deprecations = get_deprecation_messages()
    if not deprecations:
        assert deprecations == ()
    else:
        assert deprecation in get_deprecation_messages()[0]['msg']

    warnings = get_warning_messages()
    if not warning:
        assert warnings == ()
    else:
        assert warning in warnings[0]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected', 'error'),
    ((i[1:]) for i in ALIAS_TEST_CASES_INVALID),
    ids=[i[0] for i in ALIAS_TEST_CASES_INVALID]
)
def test_aliases_invalid(arg_spec, parameters, expected, error):
    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert error in result.error_messages
    assert isinstance(result.errors.errors[0], AnsibleValidationError)
    assert isinstance(result.errors, AnsibleValidationErrorMultiple)
