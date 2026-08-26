from __future__ import annotations

import typing as t

import pytest

from ansible.parsing.vault import AnsibleVaultSecretError, VaultSecret, load_vault_method

from ..test_decrypt import get_method_names
from .rot13 import patch_rot13_import


pytestmark = pytest.mark.usefixtures(patch_rot13_import.__name__)


@pytest.mark.parametrize("method_name", get_method_names())
def test_roundtrip(method_name: str) -> None:
    method = load_vault_method(method_name)

    data = b'i am some plaintext that should be encrypted'
    password = VaultSecret(b'i am a vault password')

    vaulted_value = method.encrypt(plaintext=data, secret=password, options={})

    round_tripped = method.decrypt(vaulttext=vaulted_value, secret=password)

    assert data == round_tripped


@pytest.mark.parametrize("method_name", get_method_names())
def test_failing_options(method_name: str) -> None:
    method = load_vault_method(method_name)

    with pytest.raises(TypeError) as err:
        method.encrypt(plaintext=b'blah', secret=VaultSecret(b'blah'), options=dict(invalid_option="blah"))

    assert "unexpected keyword argument 'invalid_option'" in str(err.value)


@pytest.mark.parametrize("method_name, data, secret, options, expected_output", (
    ('aes256', b'input', b'secret', dict(salt="YmFkc2FsdAo="), "3539366434363662363333323436373336343431366633640a3338643032633137393337393365306365663"
                                                               "864363330336331326136346639323566383263396562313562366635303838626336616161393436386563"
                                                               "33340a3961646464313366376533653537613162316563353333316430363266626535"),
    ('v2', b'input', b'toosmall', {}, AnsibleVaultSecretError),
    ('v2b', b'input', b'toosmall', {}, AnsibleVaultSecretError),
))
def test_encrypt_options(method_name: str, data: bytes, secret: bytes, options: dict[str, t.Any], expected_output: str | type[Exception]) -> None:
    method = load_vault_method(method_name)

    vs = VaultSecret(secret)

    if isinstance(expected_output, type) and issubclass(expected_output, Exception):
        with pytest.raises(expected_output):
            method.encrypt(plaintext=data, secret=vs, options=options)
    else:
        result = method.encrypt(plaintext=data, secret=vs, options=options)

        assert result == expected_output


@pytest.mark.parametrize("method_name", get_method_names())
def test_incorrect_password(method_name: str) -> None:
    method = load_vault_method(method_name)

    vs = VaultSecret(b'the actual correct secret')

    ciphertext = method.encrypt(plaintext=b'plaintext', secret=vs, options={})

    with pytest.raises(AnsibleVaultSecretError):
        method.decrypt(vaulttext=ciphertext, secret=VaultSecret(b'not the correct secret'))
