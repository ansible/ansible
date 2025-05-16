# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import codecs
import dataclasses
import time
import typing as t

from ansible.parsing.vault import VaultSecret
from ansible.plugins.vault import VaultSecretError, VaultBase


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Params:
    kdf_sleep_sec: float = 0.25


class Vault(VaultBase):
    @staticmethod
    def _pretend_to_generate_key(params: Params) -> None:
        time.sleep(params.kdf_sleep_sec)

    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        params = Params(**options)

        self._pretend_to_generate_key(params)

        ciphertext = codecs.encode(plaintext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')
        vaulttext = base64.b64encode(ciphertext).decode()

        return vaulttext

    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:
        if secret.bytes == b'not the correct secret':
            raise VaultSecretError()

        self._pretend_to_generate_key(Params())

        ciphertext = base64.b64decode(vaulttext.encode())
        plaintext = codecs.decode(ciphertext.decode(errors='surrogateescape'), 'rot13').encode(errors='surrogateescape')

        return plaintext
