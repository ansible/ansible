from __future__ import annotations

import typing as t

import pytest

from ansible._internal import _display_utils
from ansible._internal._datatag._tags import Origin
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.parsing.vault import EncryptedString
from ansible.parsing.yaml.objects import _AnsibleMapping, _AnsibleUnicode, _AnsibleSequence
from ansible.parsing.yaml import objects


@pytest.fixture(autouse=True, scope='function')
def suppress_warnings() -> t.Generator[None]:
    with _display_utils.DeferredWarningContext(variables={}):
        yield


def test_ansible_mapping() -> None:
    from ansible.parsing.yaml.objects import AnsibleMapping

    value = dict(a=1)
    result = AnsibleMapping(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value


def test_tagged_ansible_mapping() -> None:
    from ansible.parsing.yaml.objects import AnsibleMapping

    value = Origin(description='test').tag(dict(a=1))
    result = AnsibleMapping(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value
    assert AnsibleTagHelper.tags(result) == AnsibleTagHelper.tags(value)


def test_ansible_unicode() -> None:
    from ansible.parsing.yaml.objects import AnsibleUnicode

    value = 'hello'
    result = AnsibleUnicode(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value


def test_tagged_ansible_unicode() -> None:
    from ansible.parsing.yaml.objects import AnsibleUnicode

    value = Origin(description='test').tag('hello')
    result = AnsibleUnicode(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value
    assert AnsibleTagHelper.tags(result) == AnsibleTagHelper.tags(value)


def test_ansible_sequence() -> None:
    from ansible.parsing.yaml.objects import AnsibleSequence

    value = [1, 2, 3]
    result = AnsibleSequence(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value


def test_tagged_ansible_sequence() -> None:
    from ansible.parsing.yaml.objects import AnsibleSequence

    value = Origin(description='test').tag([1, 2, 3])
    result = AnsibleSequence(value)

    assert type(result) is type(value)  # pylint: disable=unidiomatic-typecheck
    assert result == value
    assert AnsibleTagHelper.tags(result) == AnsibleTagHelper.tags(value)


def test_ansible_vault_encrypted_unicode() -> None:
    from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode

    value = 'ciphertext'
    result = AnsibleVaultEncryptedUnicode(value)

    assert type(result) is EncryptedString  # pylint: disable=unidiomatic-typecheck
    assert result._ciphertext == value


def test_tagged_ansible_vault_encrypted_unicode() -> None:
    from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode

    value = Origin(description='test').tag('ciphertext')
    result = AnsibleVaultEncryptedUnicode(value)

    assert type(result) is EncryptedString  # pylint: disable=unidiomatic-typecheck
    assert result._ciphertext == value
    assert AnsibleTagHelper.tags(result) == AnsibleTagHelper.tags(value)


def test_invalid_attribute() -> None:
    with pytest.raises(ImportError, match="cannot import name 'bogus' from 'ansible.parsing.yaml.objects'"):
        from ansible.parsing.yaml.objects import bogus

    with pytest.raises(AttributeError, match="module 'ansible.parsing.yaml.objects' has no attribute 'bogus'"):
        assert objects.bogus


def test_non_ansible_attribute() -> None:
    with pytest.raises(ImportError, match="cannot import name 't' from 'ansible.parsing.yaml.objects'"):
        from ansible.parsing.yaml.objects import t

    with pytest.raises(AttributeError, match="module 'ansible.parsing.yaml.objects' has no attribute 't'"):
        assert objects.t


@pytest.mark.parametrize("target_type,args,kwargs,expected", (
    (_AnsibleMapping, (), {}, {}),
    (_AnsibleMapping, (dict(a=1),), {}, dict(a=1)),
    (_AnsibleMapping, (dict(a=1),), dict(b=2), dict(a=1, b=2)),
    (_AnsibleUnicode, (), {}, ''),
    (_AnsibleUnicode, ('Hello',), {}, 'Hello'),
    (_AnsibleUnicode, (), dict(object='Hello'), 'Hello'),
    (_AnsibleUnicode, (b'Hello',), {}, str(b'Hello')),
    (_AnsibleUnicode, (b'Hello',), dict(encoding='utf-8', errors='strict'), 'Hello'),
    (_AnsibleSequence, (), {}, []),
    (_AnsibleSequence, ([1, 2],), {}, [1, 2]),
))
def test_objects(target_type: type, args: tuple, kwargs: dict, expected: object) -> None:
    """Verify legacy objects support the same constructor args as their base types."""
    result = target_type(*args, **kwargs)

    assert isinstance(result, type(expected))
    assert result == expected
