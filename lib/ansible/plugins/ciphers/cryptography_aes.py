
from binascii import unhexlify
from hashlib import md5
from hashlib import sha256

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text

from ansible.plugins.ciphers import VaultCipherBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

HAS_CRYPTOGRAPHY = False
try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
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


class VaultCipher(VaultCipherBase):
    implementation = 'cryptography'
    name = 'AES'

    # this version has been obsoleted by the VaultAES256 class
    # which uses encrypt-then-mac (fixing order) and also improving the KDF used
    # code remains for upgrade purposes only
    # http://stackoverflow.com/a/16761459

    # Note: strings in this class should be byte strings by default.

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

        b_vaultdata = unhexlify(b_vaulttext)
        b_tmpsalt = b_vaultdata[:16]
        b_ciphertext = b_vaultdata[16:]

        bs = algorithms.AES.block_size // 8
        b_salt = b_tmpsalt[len(b'Salted__'):]
        b_key, b_iv = self._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = C_Cipher(algorithms.AES(b_key), modes.CBC(b_iv), BACKEND).decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        try:
            b_plaintext = unpadder.update(
                cipher.update(b_ciphertext) + cipher.finalize()
            ) + unpadder.finalize()
        except Exception as e:
            # This is a broad except, but cryptography raises ValueError/TypeError or a set
            # of exceptions derived directly from Exception
            display.error('Exception from cryptography_aes cipher plugin while decrypting: %s' % to_text(e))
            raise AnsibleError("Decryption of deprecated vault AES format via cryptography_aes cipher plugin failed")

        # split out sha and verify decryption
        b_split_data = b_plaintext.split(b"\n", 1)
        b_this_sha = b_split_data[0]
        b_plaintext = b_split_data[1]
        b_test_sha = to_bytes(sha256(b_plaintext).hexdigest())

        if b_this_sha != b_test_sha:
            raise AnsibleError("Decryption failed")

        return b_plaintext
