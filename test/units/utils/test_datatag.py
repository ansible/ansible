from __future__ import annotations

import copy
import pickle
import typing as t

import pytest

from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.parsing.vault import EncryptedString, VaultSecretsContext, VaultSecret, VaultLib
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate, VaultedValue
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
        (Origin(path='/himom.yml', line_num=42, col_num=42), "Origin(path='/himom.yml', line_num=42, col_num=42)"),
        (TrustedAsTemplate(), "TrustedAsTemplate()"),
        (VaultedValue(ciphertext="hi mom I am a secret"), "VaultedValue(ciphertext='hi mom I am a secret')"),
    ]

    test_dataclass_tag_base_field_validation_fail_instances = [
        (Origin, dict(path=TrustedAsTemplate().tag(''))),
        (Origin, dict(line_num=TrustedAsTemplate().tag(1), path='')),
        (Origin, dict(col_num=TrustedAsTemplate().tag(1), path='')),
        (VaultedValue, dict(ciphertext=TrustedAsTemplate().tag(''))),
    ]

    test_dataclass_tag_base_field_validation_pass_instances = [
        (Origin, dict(path='/something')),
        (Origin, dict(path='/something', line_num=1)),
        (Origin, dict(path='/something', col_num=1)),
        (VaultedValue, dict(ciphertext='')),
    ]

    @classmethod
    def post_init(cls) -> None:
        ciphertext = VaultLib(None).encrypt("i am a secret", _get_test_secret()).decode()

        cls.taggable_instances += [
            EncryptedString(ciphertext=ciphertext),
        ]

    # DTFIX5: ensure we're calculating the correct set of values for this context
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
    (Origin(path="/hi"), "/hi"),
    (Origin(path="/hi", line_num=1), "/hi:1"),
    (Origin(path="/hi", line_num=1, col_num=2), "/hi:1:2"),
    (Origin(path="/hi", col_num=2), "/hi"),
    (Origin(path="/hi", line_num=0), "/hi"),
    (Origin(path="/hi", line_num=0, col_num=0), "/hi"),
    (Origin(path="/hi", col_num=0), "/hi"),
    (Origin(path="/hi", line_num=-1), "/hi"),
    (Origin(path="/hi", line_num=1, col_num=-1), "/hi:1"),
    (Origin(description='<something>'), "<something>"),
    (Origin(description='<something>', line_num=1), "<something>:1"),
    (Origin(path="/hi", description='<something>'), "/hi (<something>)"),
    (Origin(path="/hi", description='<something>', line_num=1), "/hi:1 (<something>)"),
), ids=str)
def test_origin_str(sp: Origin, value: str) -> None:
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

        origin = Origin(path="/foo", line_num=12, col_num=34)

        multi_tagged_val = origin.tag(tagged_val)
        assert tagged_val is not multi_tagged_val
        assert TrustedAsTemplate.is_tagged_on(multi_tagged_val)
        assert Origin.is_tagged_on(multi_tagged_val)
        assert TrustedAsTemplate.get_tag(multi_tagged_val) is TrustedAsTemplate()  # singleton tag type, should be reference-equal
        assert Origin.get_tag(multi_tagged_val) is origin


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
