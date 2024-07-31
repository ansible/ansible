# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import json

from dataclasses import dataclass

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
except ImportError as e:
    raise ImportError("The AESV2 cipher for ansible-vault requires the cryptography library in order to function: %s" % e)

from ansible.errors import AnsibleVaultError
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.parsing.vault.ciphers import VaultCipher
from ansible.utils.display import Display

display = Display()

PASS = {}


# slots and kw_only are 3.10 only, nice to use going forward
@dataclass
class Defaults():
    salt: bytes = b'ansible'
    length: int = 32
    n: int = 2**14
    r: int = 8
    p: int = 1
    key: bytes | None = None

    def to_dict(self):
        return self.__dict__.copy()


class VaultAESV2(VaultCipher):
    """
    Vault cipher using cryptography's fernet interface

    AES in CBC mode with a 128-bit key for encryption; using PKCS7 padding.
    HMAC using SHA256 for authentication.
    Initialization vectors are generated using os.urandom().
    SCrypt for key derivation

    This also uses dual keys, generating a key per vault
    which is encrypted by the main key (which is cached).
    """
    @classmethod
    def set_defaults(cls, options):
        return Defaults(**options).to_dict()

    @classmethod
    def _key_from_password(cls, b_password, options=None):
        ''' For the main key/supplied secret only '''

        if b_password not in PASS:
            PASS[b_password] = {}

        if options is None:
            options = {}

        o = cls.set_defaults(options)

        if o['salt'] not in PASS[b_password]:
            # derive as not in cache

            kdf = Scrypt(salt=o['salt'], length=o['length'], n=o['n'], r=o['r'], p=o['p'])
            try:
                PASS[b_password][o['salt']] = base64.urlsafe_b64encode(kdf.derive(b_password))
            except InvalidToken as e:
                raise AnsibleVaultError("Failed to derive key: %s" % e)

        return PASS[b_password][o['salt']], o

    @classmethod
    def encrypt(cls, b_plaintext, secret, salt=None, options=None):

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if salt is not None:
            display.warning('The aesv2 cipher does not support custom salts, ignoring passed in salt')

        b_password = secret.bytes
        if len(b_password) < 10:
            raise AnsibleVaultError('The aesv2 cipher requires secrets longer than 10 bytes')

        # use random key to encrypt text
        key = Fernet.generate_key()
        f = Fernet(key)
        ciphered = f.encrypt(b_plaintext)

        # now crypt random key with vault secret
        password_key, options = cls._key_from_password(b_password, options)
        p = Fernet(password_key)

        # put random key (encrypted with vault secret) in options to store in ciphered text
        options['key'] = p.encrypt(key)
        try:
            return base64.b64encode(b';'.join([ciphered, cls.encode_options(options)]))
        except InvalidToken as e:
            raise AnsibleVaultError("Failed to encrypt: %s" % e)

    @classmethod
    def decrypt(cls, b_vaulttext, secret):

        b_msg, b_options = base64.b64decode(b_vaulttext).split(b';', 2)

        options = cls.decode_options(b_options)
        if 'salt' in options and not isinstance(options['salt'], bytes):
            options['salt'] = to_bytes(options['salt'])

        password_key, options = cls._key_from_password(secret.bytes, options)

        p = Fernet(password_key)
        try:
            key = p.decrypt(to_bytes(options['key']))
        except InvalidToken as e:
            raise AnsibleVaultError("Failed to decrypt private key: %s" % e)

        f = Fernet(key)
        try:
            return f.decrypt(b_msg)
        except InvalidToken as e:
            raise AnsibleVaultError("Failed to decrypt text: %s" % e)

    @staticmethod
    def encode_options(options):
        for k in options.keys():
            if isinstance(options[k], bytes):
                options[k] = to_text(options[k], errors='surrogate_or_strict')
        return to_bytes(json.dumps(options))

    @staticmethod
    def decode_options(b_options):
        return json.loads(to_text(b_options, errors='surrogate_or_strict'))
