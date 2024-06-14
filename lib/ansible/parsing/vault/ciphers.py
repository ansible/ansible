# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import typing as t
import warnings

from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError

HAS_CRYPTOGRAPHY = False
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
    HAS_CRYPTOGRAPHY = True
except ImportError:
    pass

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleVaultError, AnsibleVaultFormatError

NEED_CRYPTO_LIBRARY = "ansible-vault requires the cryptography library in order to function"


def _unhexlify(b_data: bytes) -> bytes:
    try:
        return unhexlify(b_data)
    except (BinasciiError, TypeError) as exc:
        raise AnsibleVaultFormatError('Vault format unhexlify error', orig_exc=exc)


def parse_vaulttext_old(b_vaulttext: bytes) -> list[bytes]:
    ''' old format does double hexing, only use with versions 1.1 and 1.2
    :arg b_vaulttext: byte str containing the vaulttext (ciphertext, salt, crypted_hmac)
    :returns: A tuple of byte str of the ciphertext suitable for passing to a
        Cipher class's decrypt() function, a byte str of the salt,
        and a byte str of the crypted_hmac
    :raises: AnsibleVaultFormatError: if the vaulttext format is invalid
    '''
    b_vaulttext = _unhexlify(b_vaulttext)
    return parse_vaulttext(b_vaulttext)


def parse_vaulttext(b_vaulttext: bytes) -> list[bytes]:
    """
    :arg b_vaulttext: byte str containing the vaulttext (ciphertext, salt, crypted_hmac)
    :returns: A tuple of byte str of the ciphertext suitable for passing to a
        Cipher class's decrypt() function, a byte str of the salt,
        and a byte str of the crypted_hmac
    :raises: AnsibleVaultFormatError: if the vaulttext format is invalid
    """
    # SPLIT SALT, DIGEST, AND DATA
    try:
        b_salt, b_crypted_hmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
        b_salt = _unhexlify(b_salt)
        b_ciphertext = _unhexlify(b_ciphertext)
    except AnsibleVaultFormatError:
        raise
    except Exception as exc:
        raise AnsibleVaultFormatError('Vault encrypted text format error', orig_exc=exc)

    return b_ciphertext, b_salt, b_crypted_hmac


class VaultCipher:

    # TODO: make them take vault object
    @classmethod
    def encrypt(cls, b_plaintext: bytes, secret: str, salt: str | None = None) -> bytes:
        pass

    @classmethod
    def decrypt(cls, b_vaultedtext: bytes, secret: str) -> bytes:
        pass

    @staticmethod
    def _is_equal(b_a: bytes, b_b: bytes) -> bool:
        """
        Comparing 2 byte arrays in constant time to avoid timing attacks.
        It would be nice if there were a library for this but hey.

        http://codahale.com/a-lesson-in-timing-attacks/
        """
        if len(b_a) != len(b_b):
            return False

        result = 0
        for b_x, b_y in zip(b_a, b_b):
            result |= b_x ^ b_y
        return result == 0


class VaultAES256(VaultCipher):
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
    # Note: strings in this class should be byte strings by default.

    def __init__(self) -> t.Self:
        if not HAS_CRYPTOGRAPHY:
            raise AnsibleError(NEED_CRYPTO_LIBRARY)

    @staticmethod
    def _create_key_cryptography(b_password: bytes, b_salt: bytes, key_length: int, iv_length: int) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * key_length + iv_length,
            salt=b_salt,
            iterations=10000,
            backend=CRYPTOGRAPHY_BACKEND)
        b_derivedkey = kdf.derive(b_password)

        return b_derivedkey

    @classmethod
    def _gen_key_initctr(cls, b_password: bytes, b_salt: bytes) -> list[bytes]:
        # 16 for AES 128, 32 for AES256
        key_length = 32

        if HAS_CRYPTOGRAPHY:
            # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
            iv_length = algorithms.AES.block_size // 8

            b_derivedkey = cls._create_key_cryptography(b_password, b_salt, key_length, iv_length)
            b_iv = b_derivedkey[(key_length * 2):(key_length * 2) + iv_length]
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in initctr)')

        b_key1 = b_derivedkey[:key_length]
        b_key2 = b_derivedkey[key_length:(key_length * 2)]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext: bytes, b_key1: bytes, b_key2: bytes, b_iv: bytes):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return bytes(hexlify(b_hmac)), hexlify(b_ciphertext)

    @classmethod
    def _get_salt(cls) -> str:
        custom_salt = C.config.get_config_value('VAULT_ENCRYPT_SALT')
        if not custom_salt:
            custom_salt = os.urandom(32)
        return bytes(custom_salt)

    @classmethod
    def encrypt(cls, b_plaintext: bytes, secret: str, salt: bytes | str | None = None):

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if salt is None:
            b_salt = cls._get_salt()
        elif not salt:
            raise AnsibleVaultError('Empty or invalid salt passed to encrypt()')
        else:
            b_salt = bytes(salt)

        b_password = bytes(secret)
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in encrypt)')

        b_vaulttext = b'\n'.join([hexlify(b_salt), b_hmac, b_ciphertext])
        # Unnecessary but getting rid of it is a backwards incompatible vault
        # format change
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    @classmethod
    def _decrypt_cryptography(cls, b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        # b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)
        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(_unhexlify(b_crypted_hmac))
        except InvalidSignature as e:
            raise AnsibleVaultError('HMAC verification failed: %s' % e)

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(
            decryptor.update(b_ciphertext) + decryptor.finalize()
        ) + unpadder.finalize()

        return b_plaintext

    @classmethod
    def decrypt(cls, b_vaulttext, secret):

        b_ciphertext, b_salt, b_crypted_hmac = parse_vaulttext_old(b_vaulttext)

        # TODO: would be nice if a VaultSecret could be passed directly to _decrypt_*
        #       (move _gen_key_initctr() to a AES256 VaultSecret or VaultContext impl?)
        # though, likely needs to be python cryptography specific impl that basically
        # creates a Cipher() with b_key1, a Mode.CTR() with b_iv, and a HMAC() with sign key b_key2
        b_password = secret.bytes

        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_plaintext = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in decrypt)')

        return b_plaintext


class VaultAES256v2(VaultCipher):
    pass
