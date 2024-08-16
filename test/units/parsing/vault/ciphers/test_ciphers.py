from __future__ import annotations

import typing as t

import pytest

from ansible.parsing.vault import VaultSecret, load_vault_cipher
from ansible.parsing.vault.ciphers import VaultSecretError

from ..test_decrypt import get_cipher_names


@pytest.mark.parametrize("cipher_name", get_cipher_names())
def test_roundtrip(cipher_name: str) -> None:
    cipher = load_vault_cipher(cipher_name)

    data = b'i am some plaintext that should be encrypted'
    password = VaultSecret(b'i am a vault password')

    vaulted_value = cipher.encrypt(data, password, {})

    round_tripped = cipher.decrypt(vaulted_value, password)

    assert data == round_tripped


@pytest.mark.parametrize("cipher_name", get_cipher_names())
def test_failing_options(cipher_name: str) -> None:
    cipher = load_vault_cipher(cipher_name)

    with pytest.raises(TypeError):
        cipher.encrypt(b'blah', VaultSecret(b'blah'), dict(invalid_option="blah"))


@pytest.mark.parametrize("cipher_name, data, secret, options, expected_output", (
    ('aes256', b'input', b'secret', dict(salt="YmFkc2FsdAo="), "3539366434363662363333323436373336343431366633640a3338643032633137393337393365306365663"
                                                               "864363330336331326136346639323566383263396562313562366635303838626336616161393436386563"
                                                               "33340a3961646464313366376533653537613162316563353333316430363266626535"),
    ('aesv2', b'input', b'toosmall', {}, VaultSecretError),
))
def test_encrypt_options(cipher_name: str, data: bytes, secret: bytes, options: dict[str, t.Any], expected_output: str | type[Exception]) -> None:
    cipher = load_vault_cipher(cipher_name)

    vs = VaultSecret(secret)

    if isinstance(expected_output, type) and issubclass(expected_output, Exception):
        with pytest.raises(expected_output):
            cipher.encrypt(data, vs, options)
    else:
        result = cipher.encrypt(data, vs, options)

        assert result == expected_output


@pytest.mark.parametrize("cipher_name", get_cipher_names())
def test_incorrect_password(cipher_name: str) -> None:
    cipher = load_vault_cipher(cipher_name)

    vs = VaultSecret(b'the actual correct secret')

    ciphertext = cipher.encrypt(b'plaintext', vs, {})

    with pytest.raises(VaultSecretError):
        cipher.decrypt(ciphertext, VaultSecret(b'not the correct secret'))
