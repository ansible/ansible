from __future__ import annotations

import copy
import pickle
import typing as t

import pytest

from ansible.module_utils.datatag import AnsibleTagHelper
from ansible.parsing.vault import EncryptedString, VaultSecretsContext, VaultSecret, VaultLib
from ansible.utils.datatag.tags import AnsibleSourcePosition, NotATemplate, TrustedAsTemplate, VaultedValue
from ..module_utils.datatag.test_datatag import TestDatatagTarget as _TestDatatagTarget, Later


def _get_test_secret():
    return VaultSecret(b'secretbytesblah')


@pytest.fixture(scope='module')
def _vault_secrets_context() -> t.Generator[None]:
    """A fixture that provides a `VaultSecretsContext` populated with a single default secret under the default id."""
    VaultSecretsContext._current = None

    secret = _get_test_secret()

    VaultSecretsContext.initialize(VaultSecretsContext(secrets=[('default', secret)]))

    try:
        yield
    finally:
        VaultSecretsContext._current = None


pytestmark = pytest.mark.usefixtures('_vault_secrets_context')


class TestDatatagController(_TestDatatagTarget):
    later = t.cast(t.Self, Later(locals(), parent_type=_TestDatatagTarget))

    tag_instances_with_reprs = [
        (AnsibleSourcePosition(src='/himom.yml', line=42, col=42), "AnsibleSourcePosition(src='/himom.yml', line=42, col=42)"),
        (NotATemplate(), "NotATemplate()"),
        (TrustedAsTemplate(), "TrustedAsTemplate()"),
        (VaultedValue(ciphertext="hi mom I am a secret"), "VaultedValue(ciphertext='hi mom I am a secret')"),
    ]

    test_dataclass_tag_base_field_validation_fail_instances = [
        (AnsibleSourcePosition, dict(src=NotATemplate().tag(''))),
        (AnsibleSourcePosition, dict(line=NotATemplate().tag(1), src='')),
        (AnsibleSourcePosition, dict(col=NotATemplate().tag(1), src='')),
        (VaultedValue, dict(ciphertext=NotATemplate().tag(''))),
    ]

    test_dataclass_tag_base_field_validation_pass_instances = [
        (AnsibleSourcePosition, dict(src='/something')),
        (AnsibleSourcePosition, dict(src='/something', line=1)),
        (AnsibleSourcePosition, dict(src='/something', col=1)),
        (VaultedValue, dict(ciphertext='')),
    ]

    @classmethod
    def post_init(cls) -> None:
        ciphertext = VaultLib(None).encrypt("i am a secret", _get_test_secret()).decode()

        cls.taggable_instances += [
            EncryptedString(ciphertext=ciphertext),
        ]

    # DTFIX-MERGE: ensure we're calculating the correct set of values for this context
    @classmethod
    def container_test_cases(cls) -> list:
        return []

    # HACK: avoid `SKIPPED` notifications for inherited tests with no data
    def test_tag_copy(self) -> None:
        pass

    def test_instance_copy_roundtrip(self) -> None:
        pass

    def test_tag(self) -> None:
        pass

    @pytest.mark.autoparam(later.serializable_instances)
    def test_deepcopy_roundtrip(self, value: object):
        super().test_deepcopy_roundtrip(value)


@pytest.mark.parametrize("sp, value", (
    (AnsibleSourcePosition(src="/hi"), "/hi"),
    (AnsibleSourcePosition(src="/hi", line=1), "/hi:1"),
    (AnsibleSourcePosition(src="/hi", line=1, col=2), "/hi:1:2"),
    (AnsibleSourcePosition(src="/hi", col=2), "/hi"),
    (AnsibleSourcePosition(src="/hi", line=0), "/hi"),
    (AnsibleSourcePosition(src="/hi", line=0, col=0), "/hi"),
    (AnsibleSourcePosition(src="/hi", col=0), "/hi"),
    (AnsibleSourcePosition(src="/hi", line=-1), "/hi"),
    (AnsibleSourcePosition(src="/hi", line=1, col=-1), "/hi:1"),
    (AnsibleSourcePosition(description='<something>'), "<something>"),
    (AnsibleSourcePosition(description='<something>', line=1), "<something>:1"),
    (AnsibleSourcePosition(src="/hi", description='<something>'), "/hi (<something>)"),
    (AnsibleSourcePosition(src="/hi", description='<something>', line=1), "/hi:1 (<something>)"),
), ids=str)
def test_ansible_source_position_str(sp: AnsibleSourcePosition, value: str) -> None:
    assert str(sp) == value


def test_tag_builtins():
    values = [123, 123.45, 'a string value', tuple([1, 2, 3]), [1, 2, 3], {1, 2, 3}, dict(one=1, two=2)]

    for original_val in values:
        tagged_val = TrustedAsTemplate().tag(original_val)
        zero_tagged_val = AnsibleTagHelper.tag(original_val, [])  # should return original value, not an empty tagged obj

        assert original_val == tagged_val  # equality should pass
        assert not TrustedAsTemplate.is_tagged_on(original_val)  # immutable original value via bool check
        assert TrustedAsTemplate.get_tag(original_val) is None  # immutable original value via get_tag
        assert not AnsibleTagHelper.tags(original_val)  # immutable original value via tags

        assert TrustedAsTemplate.is_tagged_on(tagged_val)
        assert TrustedAsTemplate.get_tag(tagged_val) is TrustedAsTemplate()  # singleton tag type, should be reference-equal
        assert original_val is zero_tagged_val  # original value should reference-equal the zero-tagged value

        somedata_tag = AnsibleSourcePosition(src="/foo", line=12, col=34)

        multi_tagged_val = somedata_tag.tag(tagged_val)
        assert tagged_val is not multi_tagged_val
        assert TrustedAsTemplate.is_tagged_on(multi_tagged_val)
        assert AnsibleSourcePosition.is_tagged_on(multi_tagged_val)
        assert TrustedAsTemplate.get_tag(multi_tagged_val) is TrustedAsTemplate()  # singleton tag type, should be reference-equal
        assert AnsibleSourcePosition.get_tag(multi_tagged_val) is somedata_tag


# pylint: disable=unnecessary-lambda
@pytest.mark.parametrize("copy_expr", (
    lambda es: copy.copy(es),
    lambda es: copy.deepcopy(es),
    lambda es: pickle.loads(pickle.dumps(es)),
))
def test_encrypted_string_copies(copy_expr: t.Callable[[EncryptedString], EncryptedString]):
    """Validate that copy/deepcopy/pickle work with `EncryptedString`."""
    plaintext = "i am a secret"
    ciphertext = VaultLib(None).encrypt(plaintext, _get_test_secret()).decode()
    es = EncryptedString(ciphertext=ciphertext)
    copied_es = copy_expr(es)
    assert copied_es is not es
    assert copied_es == es


@pytest.mark.parametrize("comparison, expected", (
    ("==", True),
    ("!=", False),
    (">=", True),
    ("<=", True),
    (">", False),
    ("<", False),
))
def test_encrypted_string_binary_operators(comparison: str, expected: bool) -> None:
    """Validate binary operator behavior with permutations of plain strings and `EncryptedString` instances."""
    plaintext = "i am a secret"
    ciphertext = VaultLib(None).encrypt(plaintext, _get_test_secret()).decode()
    es = EncryptedString(ciphertext=ciphertext)
    copied_es = copy.copy(es)

    permutations = (
        (plaintext, plaintext),
        (plaintext, copied_es),
        (copied_es, plaintext),
        (es, copied_es),
    )

    for lhs, rhs in permutations:
        assert eval(f'{lhs!r} {comparison} {rhs!r}') == expected

        object.__setattr__(es, '_plaintext', None)
        object.__setattr__(copied_es, '_plaintext', None)
