# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for depresolver dataclass objects."""


from __future__ import annotations

import typing as t

import pytest

from ansible.errors import AnsibleError
from ansible.galaxy.dependency_resolution.dataclasses import Requirement, _validate_v1_source_info_schema


NO_LEADING_WHITESPACES = pytest.mark.xfail(
    reason='Does not yet support leading whitespaces',
    strict=True,
)


@pytest.mark.parametrize(
    ('collection_version_spec', 'expected_is_pinned_outcome'),
    (
        ('1.2.3-dev4', True),
        (' 1.2.3-dev4', True),
        ('=1.2.3', True),
        ('= 1.2.3', True),
        (' = 1.2.3', True),
        (' =1.2.3', True),
        ('==1.2.3', True),
        ('== 1.2.3', True),
        (' == 1.2.3', True),
        (' ==1.2.3', True),
        ('!=1.0.0', False),
        ('!= 1.0.0', False),
        pytest.param(' != 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' !=1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('>1.0.0', False),
        ('> 1.0.0', False),
        pytest.param(' > 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' >1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('>=1.0.0', False),
        ('>= 1.0.0', False),
        pytest.param(' >= 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' >=1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('<1.0.0', False),
        ('< 1.0.0', False),
        pytest.param(' < 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' <1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('*', False),
        ('* ', False),
        pytest.param(' * ', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' *', False, marks=NO_LEADING_WHITESPACES),
        ('=1.2.3,!=1.2.3rc5', True),
    ),
)
def test_requirement_is_pinned_logic(
        collection_version_spec: str,
        expected_is_pinned_outcome: bool,
) -> None:
    """Test how Requirement's is_pinned property detects pinned spec."""
    assert Requirement(
        'namespace.collection', collection_version_spec,
        None, None, None,
    ).is_pinned is expected_is_pinned_outcome


@pytest.mark.parametrize(
    ("namespace", "name", "version", "provided_arguments", "expected_errors"),
    [
        (
            # Empty data
            "foo",
            "bar",
            "1.2.3",
            {},
            [],
        ),
        (
            # Correct data
            "foo",
            "bar",
            "1.2.3",
            {
                "format_version": "1.0.0",
                "download_url": "asdf",
                "version_url": "asdf",
                "server": "asdf",
                "signatures": [
                    {
                        "signature": "asdf",
                        "pubkey_fingerprint": "asdf",
                        "signing_service": "asdf",
                        "pulp_created": "asdf",
                    },
                ],
                "name": "bar",
                "namespace": "foo",
                "version": "1.2.3",
            },
            [],
        ),
        (
            # Random data that is convertible to string, but not a string
            "foo",
            "bar",
            "1.2.3",
            {
                "format_version": "1.0.0",
                "download_url": 123,
                "version_url": 1.23,
                "server": True,
                "signatures": [
                    {
                        "signature": [],
                        "pubkey_fingerprint": {},
                        "signing_service": None,
                        "pulp_created": 42,
                    },
                ],
                "name": "bar",
                "namespace": "foo",
                "version": "1.2.3",
            },
            [],
        ),
        (
            # Invalid data 1
            "foo",
            "bar",
            "1.2.3",
            {
                "format_version": 123,
                "signatures": "a,b,c",
                "name": "asdf",
                "namespace": "fdsa",
                "version": "asdffdsa",
            },
            [
                'dictionary requested, could not parse JSON or key=value',
                "Elements value for option 'signatures' is of type str and we were unable to convert "
                "to dict: dictionary requested, could not parse JSON or key=value",
                "Elements value for option 'signatures' is of type str and we were unable to convert "
                "to dict: dictionary requested, could not parse JSON or key=value",
                "Elements value for option 'signatures' is of type str and we were unable to convert "
                "to dict: dictionary requested, could not parse JSON or key=value",
                'value of format_version must be one of: 1.0.0, got: 123',
                'value of name must be one of: bar, got: asdf',
                'value of namespace must be one of: foo, got: fdsa',
                'value of version must be one of: 1.2.3, got: asdffdsa',
            ],
        ),
        (
            # Invalid data 2
            "foo",
            "bar",
            "1.2.3",
            {
                "format_version": 123,
                "signatures": {},
                "name": "asdf",
                "namespace": "fdsa",
                "version": "asdffdsa",
            },
            [
                "argument 'signatures' is of type dict and we were unable to convert to list: <class 'dict'> cannot be converted to a list",
                'value of format_version must be one of: 1.0.0, got: 123',
                'value of name must be one of: bar, got: asdf',
                'value of namespace must be one of: foo, got: fdsa',
                'value of version must be one of: 1.2.3, got: asdffdsa',
            ],
        ),
        (
            # Invalid data 3
            "foo",
            "bar",
            "1.2.3",
            {
                "signatures": [
                    {
                        "foo": 1,
                    },
                    {
                        "signature": None,
                    },
                    True,
                ],
            },
            [
                "Value 'True' in the sub parameter field 'signatures' must be a list, not 'bool'",
                "Elements value for option 'signatures' is of type bool and we were unable "
                "to convert to dict: <class 'bool'> cannot be converted to a dict",
                'signatures.foo. Supported parameters include: pubkey_fingerprint, pulp_created, signature, signing_service.',
            ],
        ),
        (
            # Unknown parameters
            "foo",
            "bar",
            "1.2.3",
            {
                "asdf": 123,
                "meh": {},
                "a": [],
            },
            [
                'a, asdf, meh. Supported parameters include: download_url, format_version, '
                'name, namespace, server, signatures, version, version_url.',
            ],
        ),
    ],
)
def test__validate_v1_source_info_schema(
    namespace: str,
    name: str,
    version: str,
    provided_arguments: dict[str, object],
    expected_errors: list[str],
) -> None:
    result = _validate_v1_source_info_schema(namespace, name, version, provided_arguments)
    assert result == expected_errors


@pytest.mark.parametrize(
    ("provided_arguments",),
    [
        (None,),
        ("asdf",),
        (123,),
        (1.2,),
        (True,),
        ([],),
    ],
)
def test__validate_v1_source_info_schema_fail(provided_arguments: t.Any) -> None:
    with pytest.raises(AnsibleError, match="^Invalid offline source info for foo.bar:1.2.3, expected a dict and got "):
        _validate_v1_source_info_schema("foo", "bar", "1.2.3", provided_arguments)
