# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2016, Adrian Likins <alikins@redhat.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from io import BytesIO

from binascii import hexlify
from binascii import unhexlify

from hashlib import md5
from hashlib import sha256

import os

# Note: Only used for loading obsolete VaultAES files.  All files are written
# using the newer VaultAES256 which does not require md5

try:
    from Crypto.Hash import SHA256, HMAC
    HAS_HASH = True
except ImportError:
    HAS_HASH = False

# Counter import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Util import Counter
    HAS_COUNTER = True
except ImportError:
    HAS_COUNTER = False

# KDF import fails for 2.0.1, requires >= 2.6.1 from pip
try:
    from Crypto.Protocol.KDF import PBKDF2
    HAS_PBKDF2 = True
except ImportError:
    HAS_PBKDF2 = False

# AES IMPORTS
try:
    from Crypto.Cipher import AES as AES
    HAS_AES = True
except ImportError:
    HAS_AES = False

from ansible.errors import AnsibleError

from ansible.module_utils.six import PY3, binary_type
from ansible.module_utils.six.moves import zip
from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# OpenSSL pbkdf2_hmac
HAS_PBKDF2HMAC = False
try:
    from cryptography.hazmat.primitives.hashes import SHA256 as c_SHA256
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    HAS_PBKDF2HMAC = True
except ImportError:
    pass
except Exception as e:
    display.vvvv("Optional dependency 'cryptography' raised an exception, falling back to 'Crypto'.")
    import traceback
    display.vvvv("Traceback from import of cryptography was {0}".format(traceback.format_exc()))

HAS_ANY_PBKDF2HMAC = HAS_PBKDF2 or HAS_PBKDF2HMAC

CRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform." \
    " You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"


def check_prereqs():
    if not HAS_AES or not HAS_COUNTER or not HAS_ANY_PBKDF2HMAC or not HAS_HASH:
        raise AnsibleError(CRYPTO_UPGRADE)


class VaultAES:
    name = 'AES'

    # this version has been obsoleted by the VaultAES256 class
    # which uses encrypt-then-mac (fixing order) and also improving the KDF used
    # code remains for upgrade purposes only
    # http://stackoverflow.com/a/16761459

    # Note: strings in this class should be byte strings by default.

    @staticmethod
    def check_prereqs():
        return check_prereqs()

    def __init__(self):
        if not HAS_AES:
            raise AnsibleError(CRYPTO_UPGRADE)

    def _aes_derive_key_and_iv(self, b_password, b_salt, key_length, iv_length):

        """ Create a key and an initialization vector """

        b_d = b_di = b''
        while len(b_d) < key_length + iv_length:
            b_text = b''.join([b_di, b_password, b_salt])
            b_di = to_bytes(md5(b_text).digest(), errors='strict')
            b_d += b_di

        b_key = b_d[:key_length]
        b_iv = b_d[key_length:key_length + iv_length]

        return b_key, b_iv

    def encrypt(self, b_plaintext, b_password, key_length=32):

        """ Read plaintext data from in_file and write encrypted to out_file """

        raise AnsibleError("Encryption disabled for deprecated VaultAES class")

    def decrypt(self, b_vaulttext, b_password, key_length=32):

        """ Decrypt the given data and return it
        :arg b_data: A byte string containing the encrypted data
        :arg b_password: A byte string containing the encryption password
        :arg key_length: Length of the key
        :returns: A byte string containing the decrypted data
        """

        display.deprecated(u'The VaultAES format is insecure and has been '
                           'deprecated since Ansible-1.5.  Use vault rekey FILENAME to '
                           'switch to the newer VaultAES256 format', version='2.3')
        # http://stackoverflow.com/a/14989032
        self.check_prereqs()

        b_ciphertext = unhexlify(b_vaulttext)

        in_file = BytesIO(b_ciphertext)
        in_file.seek(0)
        out_file = BytesIO()

        bs = AES.block_size
        b_tmpsalt = in_file.read(bs)
        b_salt = b_tmpsalt[len(b'Salted__'):]
        b_key, b_iv = self._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = AES.new(b_key, AES.MODE_CBC, b_iv)
        b_next_chunk = b''
        finished = False

        while not finished:
            b_chunk, b_next_chunk = b_next_chunk, cipher.decrypt(in_file.read(1024 * bs))
            if len(b_next_chunk) == 0:
                if PY3:
                    padding_length = b_chunk[-1]
                else:
                    padding_length = ord(b_chunk[-1])

                b_chunk = b_chunk[:-padding_length]
                finished = True

            out_file.write(b_chunk)
            out_file.flush()

        # reset the stream pointer to the beginning
        out_file.seek(0)
        b_out_data = out_file.read()
        out_file.close()

        # split out sha and verify decryption
        b_split_data = b_out_data.split(b"\n", 1)
        b_this_sha = b_split_data[0]
        b_plaintext = b_split_data[1]
        b_test_sha = to_bytes(sha256(b_plaintext).hexdigest())

        if b_this_sha != b_test_sha:
            raise AnsibleError("Decryption failed")

        return b_plaintext


class VaultAES256:
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """

    name = 'AES256'
    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

    @staticmethod
    def check_prereqs():
        return check_prereqs()

    @staticmethod
    def _create_key(b_password, b_salt, keylength, ivlength):
        hash_function = SHA256

        # make two keys and one iv
        def pbkdf2_prf(p, s):
            return HMAC.new(p, s, hash_function).digest()

        b_derivedkey = PBKDF2(b_password, b_salt, dkLen=(2 * keylength) + ivlength,
                              count=10000, prf=pbkdf2_prf)
        return b_derivedkey

    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        keylength = 32

        # match the size used for counter.new to avoid extra work
        ivlength = 16

        if HAS_PBKDF2HMAC:
            backend = default_backend()
            kdf = PBKDF2HMAC(
                algorithm=c_SHA256(),
                length=2 * keylength + ivlength,
                salt=b_salt,
                iterations=10000,
                backend=backend)
            b_derivedkey = kdf.derive(b_password)
        else:
            b_derivedkey = cls._create_key(b_password, b_salt, keylength, ivlength)

        b_key1 = b_derivedkey[:keylength]
        b_key2 = b_derivedkey[keylength:(keylength * 2)]
        b_iv = b_derivedkey[(keylength * 2):(keylength * 2) + ivlength]

        return b_key1, b_key2, hexlify(b_iv)

    def encrypt(self, b_plaintext, b_password):
        self.check_prereqs()

        b_salt = os.urandom(32)
        b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)

        # PKCS#7 PAD DATA http://tools.ietf.org/html/rfc5652#section-6.3
        bs = AES.block_size
        padding_length = (bs - len(b_plaintext) % bs) or bs
        b_plaintext += to_bytes(padding_length * chr(padding_length), encoding='ascii', errors='strict')

        # COUNTER.new PARAMETERS
        # 1) nbits (integer) - Length of the counter, in bits.
        # 2) initial_value (integer) - initial value of the counter. "iv" from _gen_key_initctr

        ctr = Counter.new(128, initial_value=int(b_iv, 16))

        # AES.new PARAMETERS
        # 1) AES key, must be either 16, 24, or 32 bytes long -- "key" from _gen_key_initctr
        # 2) MODE_CTR, is the recommended mode
        # 3) counter=<CounterObject>

        cipher = AES.new(b_key1, AES.MODE_CTR, counter=ctr)

        # ENCRYPT PADDED DATA
        b_ciphertext = cipher.encrypt(b_plaintext)

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC.new(b_key2, b_ciphertext, SHA256)
        b_vaulttext = b'\n'.join([hexlify(b_salt), to_bytes(hmac.hexdigest()), hexlify(b_ciphertext)])
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    def decrypt(self, b_vaulttext, b_password):
        self.check_prereqs()

        # SPLIT SALT, DIGEST, AND DATA
        b_vaulttext = unhexlify(b_vaulttext)
        b_salt, b_cryptedHmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
        b_salt = unhexlify(b_salt)
        b_ciphertext = unhexlify(b_ciphertext)
        b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)

        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmacDecrypt = HMAC.new(b_key2, b_ciphertext, SHA256)
        if not self._is_equal(b_cryptedHmac, to_bytes(hmacDecrypt.hexdigest())):
            return None
        # SET THE COUNTER AND THE CIPHER
        ctr = Counter.new(128, initial_value=int(b_iv, 16))
        cipher = AES.new(b_key1, AES.MODE_CTR, counter=ctr)

        # DECRYPT PADDED DATA
        b_plaintext = cipher.decrypt(b_ciphertext)

        # UNPAD DATA
        if PY3:
            padding_length = b_plaintext[-1]
        else:
            padding_length = ord(b_plaintext[-1])

        b_plaintext = b_plaintext[:-padding_length]
        return b_plaintext

    @staticmethod
    def _is_equal(b_a, b_b):
        """
        Comparing 2 byte arrrays in constant time
        to avoid timing attacks.

        It would be nice if there was a library for this but
        hey.
        """
        if not (isinstance(b_a, binary_type) and isinstance(b_b, binary_type)):
            raise TypeError('_is_equal can only be used to compare two byte strings')

        # http://codahale.com/a-lesson-in-timing-attacks/
        if len(b_a) != len(b_b):
            return False

        result = 0
        for b_x, b_y in zip(b_a, b_b):
            if PY3:
                result |= b_x ^ b_y
            else:
                result |= ord(b_x) ^ ord(b_y)
        return result == 0
