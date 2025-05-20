# DTFIX5: review this test for removal, should have been superseded by test_serialization_profiles.py
#  some tests will need to be under module_utils to verify target-only Python versions
#  if kept, de-dupe
from __future__ import annotations

import json
import typing as t
import collections.abc as c

import pytest

from ansible.module_utils._internal._datatag import AnsibleTaggedObject, _untaggable_types, AnsibleTagHelper
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.module_utils.common.json import get_encoder, get_decoder
from ansible.module_utils._internal._json._profiles import _module_legacy_m2c, _tagless, _module_legacy_c2m, _module_modern_c2m, _module_modern_m2c
from ansible._internal._json._profiles import _legacy

_simple_json_values = (
    'hello',
    1.1,
    1,
    True,
    None,
    [1],
    dict(k='v'),
)

_converted_json_values = (
    ((1,), [1]),
    ({1}, [1]),
)

origin = Origin(path='/absolute/path/for/testing')


@pytest.mark.parametrize("value, expected", _converted_json_values, ids=str)
def test_modern_controller_to_module_converted_types(value: t.Any, expected: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _module_modern_c2m
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == expected
    assert tagged_value == expected

    assert_has_no_tags(result)


@pytest.mark.parametrize("value, expected", _converted_json_values, ids=str)
def test_legacy_controller_to_module_converted_types(value: t.Any, expected: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _module_legacy_c2m
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == expected
    assert tagged_value == expected

    assert_has_no_tags(result)


@pytest.mark.parametrize("value, expected", _converted_json_values, ids=str)
def test_modern_module_to_controller_converted_types(value: t.Any, expected: t.Any) -> None:
    deprecation_tag = Deprecated(msg='go away')
    args = dict(untagged_value=value, tagged_value=deprecation_tag.tag(value))
    profile = _module_modern_m2c
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == expected
    assert tagged_value == expected

    assert_has_no_tags(untagged_value)

    if type(value) not in _untaggable_types:
        tags = AnsibleTagHelper.tags(tagged_value)

        assert tags == {deprecation_tag}


@pytest.mark.parametrize("value, expected", _converted_json_values, ids=str)
def test_legacy_module_to_controller_converted_types(value: t.Any, expected: t.Any) -> None:
    args = dict(untagged_value=value)
    profile = _module_modern_m2c
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']

    assert untagged_value == expected

    assert_has_no_tags(result)


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_modern_controller_to_module(value: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _module_modern_c2m
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == value
    assert tagged_value == value

    assert_has_no_tags(result)


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_legacy_controller_to_module(value: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _module_legacy_c2m
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == value
    assert tagged_value == value

    assert_has_no_tags(result)


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_modern_module_to_controller(value: t.Any) -> None:
    deprecation_tag = Deprecated(msg='go away')
    args = dict(
        untagged_value=value,
        tagged_value=deprecation_tag.tag(value),
        # tagged_with_unwanted_tag_only=origin.tag(value),
    )
    profile = _module_modern_m2c
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']
    # tagged_with_unwanted_tag_only = result['tagged_with_unwanted_tag_only']

    assert untagged_value == value
    assert tagged_value == value
    # assert tagged_with_unwanted_tag_only == value

    assert_has_no_tags(untagged_value)
    # assert_has_no_tags(tagged_with_unwanted_tag_only)

    if type(value) not in _untaggable_types:
        tags = AnsibleTagHelper.tags(tagged_value)

        assert tags == {deprecation_tag}


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_legacy_module_to_controller(value: t.Any) -> None:
    # deprecation_tag = Deprecated(msg='go away')
    args = dict(
        untagged_value=value,
        # tagged_value=deprecation_tag.tag(value),
        # tagged_with_unwanted_tag_only=origin.tag(value),
    )
    profile = _module_legacy_m2c
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    # tagged_value = result['tagged_value']
    # tagged_with_unwanted_tag_only = result['tagged_with_unwanted_tag_only']

    assert untagged_value == value
    # assert tagged_value == value
    # assert tagged_with_unwanted_tag_only == value

    assert_has_no_tags(untagged_value)
    # assert_has_no_tags(tagged_value)
    # assert_has_no_tags(tagged_with_unwanted_tag_only)


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_legacy(value: t.Any) -> None:
    args = dict(
        untagged_value=value,
        tagged_value=origin.tag(value),
        trusted_value=apply_trust(value),
    )
    profile = _legacy
    payload = json.dumps(args, cls=get_encoder(profile))
    payload = TrustedAsTemplate().tag(payload)
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']
    trusted_value = result['trusted_value']

    assert untagged_value == value
    assert tagged_value == value
    assert trusted_value == value

    assert_has_no_tags(untagged_value)
    assert_has_no_tags(tagged_value)
    assert_has_trusted_strings(trusted_value)


@pytest.mark.parametrize("value, expected", (
    ((1,), [1]),
    ({1}, [1]),
), ids=str)
def test_legacy_converted_types(value: t.Any, expected: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _legacy
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == expected
    assert tagged_value == expected

    assert_has_no_tags(result)


@pytest.mark.parametrize("value", _simple_json_values, ids=str)
def test_tagless(value: t.Any) -> None:
    args = dict(
        untagged_value=value,
        tagged_value=origin.tag(value),
        trusted_value=apply_trust(value),
    )
    profile = _tagless
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']
    trusted_value = result['trusted_value']

    assert untagged_value == value
    assert tagged_value == value
    assert trusted_value == value

    assert_has_no_tags(result)


@pytest.mark.parametrize("value, expected", _converted_json_values, ids=str)
def test_tagless_converted_types(value: t.Any, expected: t.Any) -> None:
    args = dict(untagged_value=value, tagged_value=origin.tag(value))
    profile = _tagless
    payload = json.dumps(args, cls=get_encoder(profile))
    result = json.loads(payload, cls=get_decoder(profile))

    untagged_value = result['untagged_value']
    tagged_value = result['tagged_value']

    assert untagged_value == expected
    assert tagged_value == expected

    assert_has_no_tags(result)


def apply_trust(o: t.Any) -> t.Any:
    if isinstance(o, str):
        return TrustedAsTemplate().tag(o)

    if isinstance(o, dict):
        return {key: apply_trust(value) for key, value in o.items()}

    if isinstance(o, (set, list, tuple)):
        return type(o)(apply_trust(item) for item in o)

    return o


def assert_has_trusted_strings(o: t.Any) -> None:
    assert not isinstance(o, str) or TrustedAsTemplate.is_tagged_on(o)

    if isinstance(o, c.Mapping):
        for key, value in o.items():
            assert_has_no_tags(key)
            assert_has_trusted_strings(value)
    elif not isinstance(o, str) and isinstance(o, c.Iterable):
        for item in o:
            assert_has_trusted_strings(item)


def assert_has_no_tags(o: t.Any) -> None:
    assert not isinstance(o, AnsibleTaggedObject)

    if isinstance(o, c.Mapping):
        for key, value in o.items():
            assert_has_no_tags(key)
            assert_has_no_tags(value)
    elif not isinstance(o, str) and isinstance(o, c.Iterable):
        for item in o:
            assert_has_no_tags(item)
