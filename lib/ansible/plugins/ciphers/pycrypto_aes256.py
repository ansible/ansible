# This file is part of Ansible
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

from binascii import hexlify
from binascii import unhexlify
import os

from ansible.plugins.ciphers import VaultCipherBase

from Crypto.Hash import SHA256, HMAC
# Counter import fails for 2.0.1, requires >= 2.6.1 from pip
from Crypto.Util import Counter
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES as AES

from ansible.module_utils.six import PY3, binary_type
from ansible.module_utils.six.moves import zip
from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


CRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform." \
    " You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"


def check_prereqs():
    pass


class VaultCipher(VaultCipherBase):
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """
    implementation = "PyCrypto"
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

        # TODO: consider this part of envelope? inner_envelope?
        #       could make sense that parse_envelope returns all the data needed to feed to a cipher.decrypt()
        #       in this case, ciphertext, b_salt, b_password
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
