# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import secrets
import typing as t

from cryptography.cobblestone import Cobblestone256Encryptor, Cobblestone256Decryptor
from cryptography.exceptions import InvalidTag

from .. import VaultSecret, AnsibleVaultSecretError
from . import VaultMethodBase


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Payload:
    salt: str
    key: str
    ciphertext: str


class VaultMethod(VaultMethodBase):
    """PQC-ready vault method with scrypt key-stretching + 256-bit Cobblestone KEK/DEK."""
    @classmethod
    @VaultMethodBase.lru_cache()
    def _derive_key_from_secret(cls, secret: bytes, salt: str, /) -> bytes:
        salt_bytes = base64.b85decode(salt.encode())
        derived_key = hashlib.scrypt(secret, salt=salt_bytes, n=2**14, r=8, p=1, dklen=32)

        return derived_key

    @classmethod
    @VaultMethodBase.no_options
    def encrypt(cls, *, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        salt = base64.b85encode(secrets.token_bytes(32)).decode()

        key_encryption_key = cls._derive_key_from_secret(secret.bytes, salt)
        key_encryption_cipher = Cobblestone256Encryptor(key_encryption_key, context=b"AnsibleVaultKE")

        data_encryption_key = Cobblestone256Encryptor.generate_key()
        data_encryption_cipher = Cobblestone256Encryptor(data_encryption_key, context=b"AnsibleVaultDE")

        encrypted_data_encryption_key = key_encryption_cipher.update(data_encryption_key) + key_encryption_cipher.finalize()
        encrypted_plaintext = data_encryption_cipher.update(plaintext) + data_encryption_cipher.finalize()

        payload = Payload(
            salt=salt,
            key=base64.b64encode(encrypted_data_encryption_key).decode(),
            ciphertext=base64.b64encode(encrypted_plaintext).decode(),
        )

        return base64.b64encode(json.dumps(dataclasses.asdict(payload)).encode()).decode()

    @classmethod
    def decrypt(cls, *, vaulttext: str, secret: VaultSecret) -> bytes:
        payload = Payload(**json.loads(base64.b64decode(vaulttext.encode()).decode()))

        key_encryption_key = cls._derive_key_from_secret(secret.bytes, payload.salt)
        key_encryption_cipher = Cobblestone256Decryptor(key_encryption_key, context=b"AnsibleVaultKE")

        try:
            data_encryption_key = key_encryption_cipher.update(base64.b64decode(payload.key.encode())) + key_encryption_cipher.finalize()
        except InvalidTag as ex:
            raise AnsibleVaultSecretError() from ex

        data_encryption_cipher = Cobblestone256Decryptor(data_encryption_key, context=b"AnsibleVaultDE")

        return data_encryption_cipher.update(base64.b64decode(payload.ciphertext.encode())) + data_encryption_cipher.finalize()
