# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import codecs
import dataclasses
import time
import typing as t

import pytest
import pytest_mock

from ansible.parsing.vault import VaultSecret
from ansible.parsing.vault.ciphers import VaultSecretError, VaultMethodBase


@pytest.fixture
def patch_rot13_import(mocker: pytest_mock.MockerFixture) -> None:
    """Stuff a reference to this test module into runtime sys.modules to make it accessible to tests."""
    import sys

    from ansible.parsing.vault import ciphers

    patched_name = '.'.join((ciphers.__name__, __name__.rsplit('.', 1)[-1]))

    mocker.patch.dict(sys.modules, values={patched_name: sys.modules[__name__]})

    yield


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Params:
    kdf_sleep_sec: float = 0.25


class VaultMethod(VaultMethodBase):
    @staticmethod
    def _pretend_to_generate_key(params: Params) -> None:
        time.sleep(params.kdf_sleep_sec)

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        params = Params(**options)

        cls._pretend_to_generate_key(params)

        ciphertext = codecs.encode(plaintext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')
        vaulttext = base64.b64encode(ciphertext).decode()

        return vaulttext

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:
        if secret.bytes == b'not the correct secret':
            raise VaultSecretError()

        cls._pretend_to_generate_key(Params())

        ciphertext = base64.b64decode(vaulttext.encode())
        plaintext = codecs.decode(ciphertext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')

        return plaintext
