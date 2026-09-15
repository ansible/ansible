# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import secrets
import typing as t

from cryptography.fernet import Fernet, InvalidToken

from .. import VaultSecret, AnsibleVaultSecretError
from . import VaultMethodBase


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Payload:
    salt: str
    ciphertext: str


class VaultMethod(VaultMethodBase):
    @classmethod
    @VaultMethodBase.lru_cache()
    def _derive_key_from_secret(cls, secret: bytes, salt: str, /) -> bytes:
        salt_bytes = base64.b85decode(salt.encode())
        derived_key = hashlib.scrypt(secret, salt=salt_bytes, n=2**14, r=8, p=1, dklen=32)

        return base64.urlsafe_b64encode(derived_key)

    @classmethod
    @VaultMethodBase.no_options
    def encrypt(cls, *, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        salt = base64.b85encode(secrets.token_bytes(32)).decode()

        data_encryption_key = cls._derive_key_from_secret(secret.bytes, salt)
        data_encryption_cipher = Fernet(data_encryption_key)

        encrypted_plaintext = data_encryption_cipher.encrypt(plaintext)

        payload = Payload(
            salt=salt,
            ciphertext=encrypted_plaintext.decode(),
        )

        return base64.b64encode(json.dumps(dataclasses.asdict(payload)).encode()).decode()

    @classmethod
    def decrypt(cls, *, vaulttext: str, secret: VaultSecret) -> bytes:
        payload = Payload(**json.loads(base64.b64decode(vaulttext.encode()).decode()))

        data_encryption_key = cls._derive_key_from_secret(secret.bytes, payload.salt)
        data_encryption_cipher = Fernet(data_encryption_key)

        try:
            return data_encryption_cipher.decrypt(payload.ciphertext.encode())
        except InvalidToken as ex:
            raise AnsibleVaultSecretError() from ex
