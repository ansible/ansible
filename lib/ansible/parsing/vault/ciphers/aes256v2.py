# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import json
import os
import warnings

from dataclasses import dataclass
from typing import Callable

CRYPTOGRAPHY_BACKEND = None
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.hmac import HMAC
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import (
        Cipher as C_Cipher, algorithms, modes
    )
    CRYPTOGRAPHY_BACKEND = default_backend()
except ImportError as e:
    raise ImportError("The AES256V2 cipher for ansible-vault requires the cryptography library in order to function") from e

from ansible import constants as C
from ansible.errors import AnsibleVaultError
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.utils.display import Display
from ansible.parsing.vault.ciphers import VaultCipher

display = Display()
PASS = {}


@dataclass
class Defaults():
    algorithm: Callable = hashes.SHA256
    backend: Callable = CRYPTOGRAPHY_BACKEND
    key_length: int = algorithms.AES.block_size // 4  # 16 for AES 128, 32 for AES256
    iv_length: int = algorithms.AES.block_size // 8
    iterations: int = 600000  # recommended 2Q/2024
    length: int = 2 * key_length + iv_length

    def to_dict(self):
        return self.__dict__.copy()


class VaultAES256V2(VaultCipher):
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2

    http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
    Note: strings in this class should be byte strings by default.

    """

    @staticmethod
    def _create_key_cryptography(b_password, b_salt, options):
        if b_password not in PASS:
            PASS[b_password] = {}

        if b_salt not in PASS[b_password]:
            kdf = PBKDF2HMAC(
                algorithm=options['algorithm'](),
                length=options['length'],
                salt=b_salt,
                iterations=options['iterations'],
                backend=options['backend'])
            PASS[b_password][b_salt] = kdf.derive(b_password)

        return PASS[b_password][b_salt]

    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt, o):

        b_derivedkey = cls._create_key_cryptography(b_password, b_salt, o)
        b_iv = b_derivedkey[(o['key_length'] * 2):(o['key_length'] * 2) + o['iv_length']]

        b_key1 = b_derivedkey[:o['key_length']]
        b_key2 = b_derivedkey[o['key_length']:(o['key_length'] * 2)]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv, options):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), options['backend'])
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, options['algorithm'](), options['backend'])
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return b_hmac, b_ciphertext

    @staticmethod
    def _get_salt():
        # this is not safe, but won't deprecate as cipher itself will be deprecated
        custom_salt = C.config.get_config_value('VAULT_ENCRYPT_SALT')
        if not custom_salt:
            custom_salt = os.urandom(32)
        return to_bytes(custom_salt)

    @classmethod
    def encrypt(cls, b_plaintext, secret, salt=None, options=None):

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if salt is not None:
            display.warning('The aes256v2 cipher does not support custom salts, ignoring passed in salt')

        if options is None:
            options = {}
        o = Defaults(**options).to_dict()

        b_salt = cls._get_salt()
        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt, o)

        b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv, o)
        b_options = cls.encode_options(options)

        return base64.b64encode(b'\n'.join([b_salt, b_hmac, b_ciphertext, b_options]))

    @staticmethod
    def _decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv, options):
        hmac = HMAC(b_key2, options['algorithm'](), options['backend'])
        hmac.update(b_ciphertext)
        try:
            hmac.verify(b_crypted_hmac)
        except InvalidSignature as e:
            raise ValueError('HMAC verification failed') from e

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), options['backend'])
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(decryptor.update(b_ciphertext) + decryptor.finalize()) + unpadder.finalize()

        return b_plaintext

    @classmethod
    def decrypt(cls, b_vaulttext, secret):
        try:
            b_salt, b_crypted_hmac, b_ciphertext, b_options = base64.b64decode(b_vaulttext).split(b"\n", 3)
        except ValueError as e:
            raise ValueError("Invalid ciphered data in vault") from e

        options = cls.decode_options(b_options)
        o = Defaults(**options).to_dict()
        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt, o)

        b_plaintext = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv, o)

        return b_plaintext

    @staticmethod
    def encode_options(options):
        for k in options.keys():
            if isinstance(options[k], bytes):
                options[k] = to_text(options[k], errors='surrogate_or_strict')
        return to_bytes(json.dumps(options))

    @staticmethod
    def decode_options(b_options):
        return json.loads(to_text(b_options, errors='surrogate_or_strict'))
