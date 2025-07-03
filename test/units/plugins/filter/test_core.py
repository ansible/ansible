# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible._internal._datatag._tags import Origin
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.filter.core import to_bool, to_uuid
from ansible.errors import AnsibleError
from ansible.template import Templar, trust_as_template, is_trusted_as_template
from ...test_utils.controller.display import emits_warnings

UUID_DEFAULT_NAMESPACE_TEST_CASES = (
    ('example.com', 'ae780c3a-a3ab-53c2-bfb4-098da300b3fe'),
    ('test.example', '8e437a35-c7c5-50ea-867c-5c254848dbc2'),
    ('café.example', '8a99d6b1-fb8f-5f78-af86-879768589f56'),
)

UUID_TEST_CASES = (
    ('361E6D51-FAEC-444A-9079-341386DA8E2E', 'example.com', 'ae780c3a-a3ab-53c2-bfb4-098da300b3fe'),
    ('361E6D51-FAEC-444A-9079-341386DA8E2E', 'test.example', '8e437a35-c7c5-50ea-867c-5c254848dbc2'),
    ('11111111-2222-3333-4444-555555555555', 'example.com', 'e776faa5-5299-55dc-9057-7a00e6be2364'),
)


@pytest.mark.parametrize('value, expected', UUID_DEFAULT_NAMESPACE_TEST_CASES)
def test_to_uuid_default_namespace(value, expected):
    assert expected == to_uuid(value)


@pytest.mark.parametrize('namespace, value, expected', UUID_TEST_CASES)
def test_to_uuid(namespace, value, expected):
    assert expected == to_uuid(value, namespace=namespace)


def test_to_uuid_invalid_namespace():
    with pytest.raises(AnsibleError) as e:
        to_uuid('example.com', namespace='11111111-2222-3333-4444-555555555')
    assert 'Invalid value' in to_native(e.value)


@pytest.mark.parametrize('value', [None, 'nope', 1.1])
def test_to_bool_deprecation(value: object):
    with emits_warnings(deprecation_pattern='The `bool` filter coerced invalid value .+ to False'):
        to_bool(value)


@pytest.mark.parametrize("trust", (
    True,
    False,
))
def test_from_yaml_trust(trust: bool) -> None:
    """Validate trust propagation from source string."""
    value = "a: b"

    if trust:
        value = trust_as_template(value)

    result = Templar(variables=dict(value=value)).template(trust_as_template("{{ value | from_yaml }}"))

    assert result == dict(a='b')
    assert is_trusted_as_template(result['a']) is trust

    result = Templar(variables=dict(value=value)).template(trust_as_template("{{ value | from_yaml_all }}"))

    assert result == [dict(a='b')]
    assert is_trusted_as_template(result[0]['a']) is trust


def test_from_yaml_origin() -> None:
    """Validate origin propagation and position offset from source string."""
    data_with_origin = Origin(description="a unit test", line_num=42, col_num=10).tag("\n\nfoo: bar")

    templar = Templar(variables=dict(data_with_origin=data_with_origin))

    for result in [
        templar.template(trust_as_template("{{ data_with_origin | from_yaml }}")),
        templar.template(trust_as_template("{{ data_with_origin | from_yaml_all }}"))[0],
    ]:
        assert result == dict(foo="bar")

        origin = Origin.get_tag(result['foo'])

        assert origin.description == "a unit test"
        assert origin.line_num == 44  # source string origin plus two blank lines
        assert origin.col_num == 6
