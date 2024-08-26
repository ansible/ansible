# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import dataclasses
import hashlib
import hmac  # if we got to sha3 we should switch to kmac
import json
import secrets
import typing as t

from cryptography.fernet import Fernet, InvalidToken

from .. import VaultSecret
from . import VaultMethodBase, VaultSecretError


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class NoParams:
    """No options accepted. Any options provided will result in an error."""


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Params:
    """Default options for this VaultMethod."""
    salt: str
    length: int = 32
    n: int = 2**14  # iterations (cpu + mem)
    r: int = 8  # block size (mem)
    p: int = 1  # paralelism (cpu + mem)


class VaultMethod(VaultMethodBase):

    @classmethod
    @VaultMethodBase.lru_cache()
    def _derive_key_encryption_key_from_secret(cls, secret: bytes, params: Params, /) -> bytes:
        return cls._derive_key_encryption_key_from_secret_no_cache(secret, params)

    @classmethod
    def _derive_key_encryption_key_from_secret_no_cache(cls, secret: bytes, params: Params, /) -> bytes:
        if len(secret) < 10:
            # TODO: require complexity?
            raise VaultSecretError(f"The vault secret must be at least 10 bytes (received {len(secret)}).")

        salt = base64.b64decode(params.salt.encode())
        derived_key = hashlib.scrypt(secret, salt=salt, n=params.n, r=params.r, p=params.p, dklen=params.length)

        return base64.urlsafe_b64encode(derived_key)

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        NoParams(**options)  # no options accepted
        salt = base64.b64encode(secrets.token_bytes(64)).decode()
        params = Params(salt=salt)

        data_encryption_key = cls._derive_key_encryption_key_from_secret_no_cache(secret.bytes, params)
        data_encryption_cipher = Fernet(data_encryption_key)
        encrypted_text = data_encryption_cipher.encrypt(plaintext)
        digest = base64.b64encode(hmac.digest(data_encryption_key, encrypted_text, hashlib.sha512))

        payload = dict(
            salt=salt,
            digest=digest.decode(),
            ciphertext=encrypted_text.decode(),
        )

        return base64.b64encode(json.dumps(payload).encode()).decode()

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:
        payload = json.loads(base64.b64decode(vaulttext.encode()).decode())
        params = Params(salt=payload['salt'])

        data_encryption_key = cls._derive_key_encryption_key_from_secret(secret.bytes, params)
        digest = base64.b64decode(payload['digest'].encode())
        verify = hmac.digest(data_encryption_key, payload['ciphertext'].encode(), hashlib.sha512)
        if not secrets.compare_digest(digest, verify):
            raise VaultSecretError("not the correct secret")

        data_encryption_cipher = Fernet(data_encryption_key)

        try:
            return data_encryption_cipher.decrypt(payload['ciphertext'].encode())
        except InvalidToken as e:
            raise VaultSecretError("not the correct secret") from e
