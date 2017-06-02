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

from binascii import hexlify
from binascii import unhexlify
import os


from ansible.errors import AnsibleError

from ansible.plugins.ciphers import VaultCipherBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

HAS_CRYPTOGRAPHY = False
try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.hmac import HMAC
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import (
        Cipher as C_Cipher, algorithms, modes
    )
    HAS_CRYPTOGRAPHY = True
except ImportError:
    # TODO: log/display something?
    pass
except Exception as e:
    display.vvvv("Optional dependency 'cryptography' raised an exception, falling back to 'Crypto'.")
    import traceback
    display.vvvv("Traceback from import of cryptography was {0}".format(traceback.format_exc()))


BACKEND = default_backend()


def check_prereqs():
    if not HAS_CRYPTOGRAPHY:
        raise AnsibleError("ansible-vault requires the 'cryptography' python module to be installed.")


class VaultCipher(VaultCipherBase):

    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """
    implementation = 'cryptography'
    name = 'AES256'

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

    @staticmethod
    def check_prereqs():
        return check_prereqs()

    @staticmethod
    def _create_key(b_password, b_salt, keylength, ivlength):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * keylength + ivlength,
            salt=b_salt,
            iterations=10000,
            backend=BACKEND)
        b_derivedkey = kdf.derive(b_password)

        return b_derivedkey

    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        keylength = 32

        # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
        ivlength = algorithms.AES.block_size // 8

        b_derivedkey = cls._create_key(b_password, b_salt, keylength, ivlength)

        b_key1 = b_derivedkey[:keylength]
        b_key2 = b_derivedkey[keylength:(keylength * 2)]
        b_iv = b_derivedkey[(keylength * 2):(keylength * 2) + ivlength]

        return b_key1, b_key2, b_iv

    def encrypt(self, b_plaintext, b_password):
        display.v('Using cryptography_aes for AES256 encrypt')
        b_salt = os.urandom(32)
        b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), BACKEND)
        hmac.update(b_ciphertext)
        b_vaulttext = b'\n'.join([hexlify(b_salt), hexlify(hmac.finalize()), hexlify(b_ciphertext)])
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    def decrypt(self, b_vaulttext, b_password):
        display.v('Using cryptography_aes for AES256 decrypt')
        # SPLIT SALT, DIGEST, AND DATA
        b_vaulttext = unhexlify(b_vaulttext)
        b_salt, b_cryptedHmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
        b_salt = unhexlify(b_salt)
        b_ciphertext = unhexlify(b_ciphertext)
        b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)

        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac = HMAC(b_key2, hashes.SHA256(), BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(unhexlify(b_cryptedHmac))
        except InvalidSignature:
            return None

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(
            decryptor.update(b_ciphertext) + decryptor.finalize()
        ) + unpadder.finalize()

        return b_plaintext
