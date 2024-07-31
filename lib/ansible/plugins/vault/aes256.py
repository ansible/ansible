# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

DOCUMENTATION = """
    name: aes256
    version_added: "2.4"
    short_description: AES256 and PBKDF2HMAC
    description:
        - AES256 with PBKDF2HMAC key derivation and double hexlify byte shield/armor.
    requirements:
        - cryptography (python)
    options:
        salt:
            description:
                - Encryption salt to use, if not set it will be random.
                - This is mostly here for having a reproducible result when testing and should not be set in production use.
            type: str
            deprecated:
                why: While disabled by default, a lot of samples using a common salt can make it easy for attackers to deduce the vault secret
                alternatives: None, a random salt will always be generated
                removed_in: '2.22'
            version_added: '2.15'
            ini:
            - {key: salt, section: aes256_vault}
            - {key: vault_encrypt_salt, section: defaults}
            env:
            - name: ANSIBLE_VAULT_AES256_SALT
            - name: ANSIBLE_VAULT_ENCRYPT_SALT
        iterations:
            description:
                - Number of passes to do for deriving keys, the higher the number the more secure.
            type: int
            default: 600000
            ini:
            - key: iterations
              section: aes256_vault
            env:
            - name: ANSIBLE_VAULT_AES256_ITERATIONS
        key_length:
            description: Lentgh of derived key
            type: int
            default: 32
    notes:
    - The plugin is new in 2.19, but the code itself was added in 2.4 and was the hardcoded default.
    - Increasing iterations or key_lenght also increases CPU usage and encryption/decryption times.
    - Current defaults are considered safe at the time this plugin was published
    - The previous 'hardcoded' vault used this plugin with the 'version 1' settings,
      iterations set to 10000, but that is considered unsafe at the time of writing.
"""

import os
import json
import typing as t

from binascii import hexlify, unhexlify
try:
    from cryptography.exceptions import InvalidSignature
    # hazmat can cause import errors, handled by caller
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.ciphers import Cipher as C_Cipher, algorithms, modes
    from cryptography.hazmat.primitives.hmac import HMAC
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPT_IMPORT_ERROR = None
except Exception as e:
    # not using importerror as crypto libraries frequently issue different exceptions, specially under FIPS
    CRYPT_IMPORT_ERROR = e

from ansible.utils.display import Display


from ansible.parsing.vault import VaultSecret
from . import VaultBase, VaultSecretError


class Vault(VaultBase):
    """Vault implementation using AES-CTR with an HMAC-SHA256 authentication code. Keys are derived using PBKDF2."""

    _V1_OPTIONS = {'iterations': 10_000, 'key_length': 32}

    def __init__(self):

        if CRYPT_IMPORT_ERROR is not None:
            VaultBase._import_error('cryptography', CRYPT_IMPORT_ERROR)

        super().__init__()

        self.CRYPTOGRAPHY_BACKEND = default_backend()

    @VaultBase.lru_cache()
    def _generate_keys_and_iv(self, secret: bytes, salt: bytes) -> tuple[bytes, bytes, bytes]:

        # AES is a 128-bit block cipher, so we used a 32 byte key and 16 byte IVs and counter nonces
        key_length = self.get_option('key_length')
        iv_length = algorithms.AES.block_size // 8

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length * 2 + iv_length,
            salt=salt,
            iterations=self.get_option('iterations'),
            backend=self.CRYPTOGRAPHY_BACKEND,
        )

        derived_key = kdf.derive(secret)

        key1 = derived_key[:key_length]
        key2 = derived_key[key_length:key_length * 2]
        iv = derived_key[key_length * 2:]

        return key1, key2, iv

    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:

        self.set_options(direct=options)

        salt = self.get_option('salt')
        if salt:
            salt = salt.encode(errors='surrogateescape')
        else:
            salt = os.urandom(32)

        key1, key2, iv = self._generate_keys_and_iv(secret.bytes, salt)

        cipher = C_Cipher(algorithms.AES(key1), modes.CTR(iv), self.CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        ciphertext = encryptor.update(padder.update(plaintext) + padder.finalize()) + encryptor.finalize()

        hmac = HMAC(key2, hashes.SHA256(), self.CRYPTOGRAPHY_BACKEND)
        hmac.update(ciphertext)
        signature = hmac.finalize()

        # save params for decryption, except salt which goes in header
        options = self.get_options()
        del options['salt']

        # redundant double hexlify cannot be removed as it is backwards incompatible
        if options == Vault._V1_OPTIONS:
            Display().warning("Encryption with the AES256 with low iterations should only be used for backwards compatibility with older versions of Ansible.")
            # if using 'backwards compat options' omit the extra params
            ciphertext = hexlify(b'\n'.join(map(hexlify, (salt, signature, ciphertext))))
        else:
            params = json.dumps(options).encode()
            ciphertext = hexlify(b'\n'.join(map(hexlify, (salt, signature, ciphertext, params))))

        return ciphertext.decode()

    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:

        try:
            salt, signature, ciphertext, params = map(unhexlify, unhexlify(vaulttext).split(b'\n', 3))
        except ValueError:
            # must be legacy vault, doesn't have params
            salt, signature, ciphertext = map(unhexlify, unhexlify(vaulttext).split(b'\n', 2))
            params = None

        if params is None:
            # old vaults did not save params, set iterations to compatible V1 options
            options = Vault._V1_OPTIONS
        else:
            options = json.loads(params.decode())

        # options set from vault itself (or use defaults for legacy)
        self.set_options(direct=options)

        key1, key2, iv = self._generate_keys_and_iv(secret.bytes, salt)

        hmac = HMAC(key2, hashes.SHA256(), self.CRYPTOGRAPHY_BACKEND)
        hmac.update(ciphertext)

        try:
            hmac.verify(signature)
        except InvalidSignature as ex:
            raise VaultSecretError() from ex

        cipher = C_Cipher(algorithms.AES(key1), modes.CTR(iv), self.CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        return unpadder.update(decryptor.update(ciphertext) + decryptor.finalize()) + unpadder.finalize()
