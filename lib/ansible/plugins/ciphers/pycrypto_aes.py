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

from binascii import unhexlify
from io import BytesIO

from hashlib import md5
from hashlib import sha256

from ansible.plugins.ciphers import VaultCipherBase

# Note: Only used for loading obsolete VaultAES files.  All files are written
# using the newer VaultAES256 which does not require md5


# AES IMPORTS
try:
    from Crypto.Cipher import AES as AES
    HAS_AES = True
except ImportError:
    HAS_AES = False

from ansible.errors import AnsibleError

from ansible.module_utils.six import PY3
from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


CRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform." \
    " You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"


def check_prereqs():
    if not HAS_AES:
        raise AnsibleError(CRYPTO_UPGRADE)


class VaultCipher(VaultCipherBase):
    name = 'AES'
    implementation = "PyCrypto"

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
