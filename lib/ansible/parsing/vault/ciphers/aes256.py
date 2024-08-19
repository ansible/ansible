# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import dataclasses
import os
import typing as t

from binascii import hexlify, unhexlify

from cryptography.exceptions import InvalidSignature
# hazmat can cause import errors, handled by caller
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher as C_Cipher, algorithms, modes
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ansible import constants
from ansible.module_utils.common.text.converters import to_bytes

from .. import VaultSecret
from . import VaultCipherBase, VaultSecretError

CRYPTOGRAPHY_BACKEND = default_backend()


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Params:
    # kept for backwards compatibility, unsafe to reuse salts
    # was added for testing, avoid setting if possible
    salt: str = constants.config.get_config_value('VAULT_ENCRYPT_SALT')


class VaultCipher(VaultCipherBase):
    """Vault implementation using AES-CTR with an HMAC-SHA256 authentication code. Keys are derived using PBKDF2."""

    @classmethod
    @VaultCipherBase.lru_cache()
    def _generate_keys_and_iv(cls, secret: bytes, salt: bytes) -> tuple[bytes, bytes, bytes]:

        # AES is a 128-bit block cipher, so we used a 32 byte key and 16 byte IVs and counter nonces
        key_length = 32
        iv_length = algorithms.AES.block_size // 8

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length * 2 + iv_length,
            salt=salt,
            iterations=10000,  # considred weak as of 2024
            backend=CRYPTOGRAPHY_BACKEND,
        )

        derived_key = kdf.derive(secret)

        key1 = derived_key[:key_length]
        key2 = derived_key[key_length:key_length * 2]
        iv = derived_key[key_length * 2:]

        return key1, key2, iv

    @classmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        params = Params(**options)

        if params.salt:
            salt = to_bytes(params.salt, errors='surrogateescape')
        else:
            salt = os.urandom(32)

        key1, key2, iv = cls._generate_keys_and_iv(secret.bytes, salt)

        cipher = C_Cipher(algorithms.AES(key1), modes.CTR(iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        ciphertext = encryptor.update(padder.update(plaintext) + padder.finalize()) + encryptor.finalize()

        hmac = HMAC(key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(ciphertext)
        signature = hmac.finalize()

        # redundant double hexlify cannot be removed as it is backwards incompatible
        return hexlify(b'\n'.join(map(hexlify, (salt, signature, ciphertext)))).decode()

    @classmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:
        salt, signature, ciphertext = map(unhexlify, unhexlify(vaulttext).split(b'\n', 2))
        key1, key2, iv = cls._generate_keys_and_iv(secret.bytes, salt)

        hmac = HMAC(key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(ciphertext)

        try:
            hmac.verify(signature)
        except InvalidSignature as ex:
            raise VaultSecretError() from ex

        cipher = C_Cipher(algorithms.AES(key1), modes.CTR(iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        return unpadder.update(decryptor.update(ciphertext) + decryptor.finalize()) + unpadder.finalize()
