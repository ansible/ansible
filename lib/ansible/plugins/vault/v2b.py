# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

# TODO: overwrite v2 with this

DOCUMENTATION = """
    name: v2b
    version_added: "2.14"
    short_description: AES256 and Scrypt
    description:
        - AES256 with Scrypt key derivation and base64 byte shield/armor
    requirements:
        - cryptography.fernet (python)
    options:
        block_size:
            description: Block Size (r) used while deriving key
            default: 8
            type: int
            ini:
            - {key: block_size, section: v2b_vault}
            env:
            - name: ANSIBLE_VAULT_V2B_BLOCK_SIZE
        iterations:
            description: Number of iterations (n) for key derivation
            type: int
            default: 16384
            ini:
            - {key: iterations, section: v2b_vault}
            env:
            - name: ANSIBLE_VAULT_V2B_ITERATIONS
        key_length:
            description: Length of derived key in bytes
            type: int
            default: 32
            ini:
            - {key: key_length, section: v2b_vault}
            env:
            - name: ANSIBLE_VAULT_V2B_KEY_LENGTH
        parallelization:
            description: Number of parallel threads (p) to use to derive key
            default: 1
            type: int
            ini:
            - {key: parallelization, section: v2b_vault}
            env:
            - name: ANSIBLE_VAULT_V2B_KEY_PARALLELIZATION
"""

import base64
import hashlib
import hmac  # if we got to sha3 we should switch to kmac
import json
import secrets
import typing as t

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTOLIB_ERROR = None
except Exception as e:
    CRYPTOLIB_ERROR = e

from ansible.module_utils.common.text.converters import to_bytes
from ansible.parsing.vault import VaultSecret
from . import VaultBase, VaultSecretError


class Vault(VaultBase):

    def __init__(self):
        if CRYPTOLIB_ERROR:
            VaultBase._import_error('cryptography.fernet', CRYPTOLIB_ERROR)
        super().__init__()

    @VaultBase.lru_cache()
    def _derive_key_encryption_key_from_secret(self, secret: bytes, salt: bytes, /) -> bytes:
        return self._derive_key_encryption_key_from_secret_no_cache(secret, salt)

    def _derive_key_encryption_key_from_secret_no_cache(self, secret: bytes, salt: bytes, /) -> bytes:
        if len(secret) < 10:
            # TODO: require complexity?
            raise VaultSecretError(f"The vault secret must be at least 10 bytes (received {len(secret)}).")

        salt = base64.b64decode(salt)
        derived_key = hashlib.scrypt(secret, salt=salt, n=self.get_option('iterations'), r=self.get_option('block_size'),
                                     p=self.get_option('parallelization'), dklen=self.get_option('key_length'))

        return base64.urlsafe_b64encode(derived_key)

    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        self.set_options(direct=options)
        salt = to_bytes(base64.b64encode(secrets.token_bytes(64)).decode())

        data_encryption_key = self._derive_key_encryption_key_from_secret_no_cache(secret.bytes, salt)
        data_encryption_cipher = Fernet(data_encryption_key)
        encrypted_text = data_encryption_cipher.encrypt(plaintext)
        digest = base64.b64encode(hmac.digest(data_encryption_key, encrypted_text, hashlib.sha512))

        payload = dict(
            salt=salt.decode(),
            digest=digest.decode(),
            ciphertext=encrypted_text.decode(),
            options=self.get_options(),
        )

        return base64.b64encode(json.dumps(payload).encode()).decode()

    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:

        payload = json.loads(base64.b64decode(vaulttext.encode()).decode())
        salt = payload['salt']
        self.set_options(direct=payload['options'])

        data_encryption_key = self._derive_key_encryption_key_from_secret(secret.bytes, salt)
        digest = base64.b64decode(payload['digest'].encode())
        verify = hmac.digest(data_encryption_key, payload['ciphertext'].encode(), hashlib.sha512)
        if not secrets.compare_digest(digest, verify):
            raise VaultSecretError("not the correct secret")

        data_encryption_cipher = Fernet(data_encryption_key)

        try:
            return data_encryption_cipher.decrypt(payload['ciphertext'].encode())
        except InvalidToken as e:
            raise VaultSecretError("not the correct secret") from e
