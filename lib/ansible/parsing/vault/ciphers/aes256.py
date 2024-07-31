# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import os
import warnings

from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError

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
    raise ImportError("The AES256 cipher for ansible-vault requires the cryptography library in order to function: %s" % e)

from ansible import constants as C
from ansible.errors import AnsibleVaultError
from ansible.module_utils.common.text.converters import to_bytes
from ansible.utils.display import Display
from ansible.parsing.vault.ciphers import VaultCipher

display = Display()


class VaultAES256(VaultCipher):
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2

    http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
    Note: strings in this class should be byte strings by default.
    """

    @staticmethod
    def _unhexlify(b_data):
        try:
            return unhexlify(b_data)
        except (BinasciiError, TypeError) as exc:
            raise TypeError('Invalid vaulted text format, cannot unhexlify: %s' % exc)

    @staticmethod
    def _create_key_cryptography(b_password, b_salt, key_length, iv_length):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * key_length + iv_length,
            salt=b_salt,
            iterations=10000,
            backend=CRYPTOGRAPHY_BACKEND)
        return kdf.derive(b_password)

    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        key_length = 32

        # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
        iv_length = algorithms.AES.block_size // 8

        b_derivedkey = cls._create_key_cryptography(b_password, b_salt, key_length, iv_length)
        b_iv = b_derivedkey[(key_length * 2):(key_length * 2) + iv_length]

        b_key1 = b_derivedkey[:key_length]
        b_key2 = b_derivedkey[key_length:(key_length * 2)]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return b_hmac, b_ciphertext

    @staticmethod
    def _get_salt(salt):
        # this is not safe, but won't deprecate as cipher itself will be deprecated
        custom_salt = salt or C.config.get_config_value('VAULT_ENCRYPT_SALT')
        if not custom_salt:
            custom_salt = os.urandom(32)
        return to_bytes(custom_salt)

    @classmethod
    def encrypt(cls, b_plaintext, secret, salt=None, options=None):

        if secret is None:
            raise ValueError('The secret passed to encrypt() was None')

        b_salt = cls._get_salt(salt)
        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv)

        # Unnecessary x2 hexlifying but getting rid of it is a backwards incompatible change
        return hexlify(b'\n'.join([hexlify(x) for x in [b_salt, b_hmac, b_ciphertext]]))

    @staticmethod
    def _decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(b_crypted_hmac)
        except InvalidSignature as e:
            raise AnsibleVaultError('HMAC verification failed: %s' % e)

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()

        return unpadder.update(decryptor.update(b_ciphertext) + decryptor.finalize()) + unpadder.finalize()

    @classmethod
    def decrypt(cls, b_vaulttext, secret):
        try:
            b_salt, b_crypted_hmac, b_ciphertext = [cls._unhexlify(x) for x in cls._unhexlify(b_vaulttext).split(b"\n", 2)]
        except ValueError as e:
            raise ValueError("Invalid ciphered data in vault: %s" % e)

        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        return VaultAES256._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
