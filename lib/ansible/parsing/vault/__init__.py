# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2016, Adrian Likins <alikins@redhat.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
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

import os
import random
import shlex
import shutil
import sys
import tempfile
import warnings
from binascii import hexlify
from binascii import unhexlify
from hashlib import md5
from hashlib import sha256
from io import BytesIO
from subprocess import call

HAS_CRYPTOGRAPHY = False
HAS_PYCRYPTO = False
HAS_SOME_PYCRYPTO = False
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

try:
    from Crypto.Cipher import AES as AES_pycrypto
    HAS_SOME_PYCRYPTO = True

    # Note: Only used for loading obsolete VaultAES files.  All files are written
    # using the newer VaultAES256 which does not require md5
    from Crypto.Hash import SHA256 as SHA256_pycrypto
    from Crypto.Hash import HMAC as HMAC_pycrypto

    # Counter import fails for 2.0.1, requires >= 2.6.1 from pip
    from Crypto.Util import Counter as Counter_pycrypto

    # KDF import fails for 2.0.1, requires >= 2.6.1 from pip
    from Crypto.Protocol.KDF import PBKDF2 as PBKDF2_pycrypto
    HAS_PYCRYPTO = True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.module_utils.six import PY3, binary_type
from ansible.module_utils.six.moves import zip
from ansible.module_utils._text import to_bytes, to_text

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


b_HEADER = b'$ANSIBLE_VAULT'
CIPHER_WHITELIST = frozenset((u'AES', u'AES256'))
CIPHER_WRITE_WHITELIST = frozenset((u'AES256',))
# See also CIPHER_MAPPING at the bottom of the file which maps cipher strings
# (used in VaultFile header) to a cipher class

NEED_CRYPTO_LIBRARY = "ansible-vault requires either the cryptography library (preferred) or"
if HAS_SOME_PYCRYPTO:
    NEED_CRYPTO_LIBRARY += " a newer version of"
NEED_CRYPTO_LIBRARY += " pycrypto in order to function."


class AnsibleVaultError(AnsibleError):
    pass


def is_encrypted(data):
    """ Test if this is vault encrypted data blob

    :arg data: a byte or text string to test whether it is recognized as vault
        encrypted data
    :returns: True if it is recognized.  Otherwise, False.
    """
    try:
        # Make sure we have a byte string and that it only contains ascii
        # bytes.
        b_data = to_bytes(to_text(data, encoding='ascii', errors='strict', nonstring='strict'), encoding='ascii', errors='strict')
    except (UnicodeError, TypeError):
        # The vault format is pure ascii so if we failed to encode to bytes
        # via ascii we know that this is not vault data.
        # Similarly, if it's not a string, it's not vault data
        return False

    if b_data.startswith(b_HEADER):
        return True
    return False


def is_encrypted_file(file_obj, start_pos=0, count=-1):
    """Test if the contents of a file obj are a vault encrypted data blob.

    :arg file_obj: A file object that will be read from.
    :kwarg start_pos: A byte offset in the file to start reading the header
        from.  Defaults to 0, the beginning of the file.
    :kwarg count: Read up to this number of bytes from the file to determine
        if it looks like encrypted vault data.  The default is -1, read to the
        end of file.
    :returns: True if the file looks like a vault file. Otherwise, False.
    """
    # read the header and reset the file stream to where it started
    current_position = file_obj.tell()
    try:
        file_obj.seek(start_pos)
        return is_encrypted(file_obj.read(count))

    finally:
        file_obj.seek(current_position)


class VaultLib:

    def __init__(self, b_password):
        self.b_password = to_bytes(b_password, errors='strict', encoding='utf-8')
        self.cipher_name = None
        self.b_version = b'1.1'

    @staticmethod
    def is_encrypted(data):
        """ Test if this is vault encrypted data

        :arg data: a byte or text string or a python3 to test for whether it is
            recognized as vault encrypted data
        :returns: True if it is recognized.  Otherwise, False.
        """

        # This could in the future, check to see if the data is a vault blob and
        # is encrypted with a key associated with this vault
        # instead of just checking the format.
        display.deprecated(u'vault.VaultLib.is_encrypted is deprecated.  Use vault.is_encrypted instead', version='2.4')
        return is_encrypted(data)

    @staticmethod
    def is_encrypted_file(file_obj):
        display.deprecated(u'vault.VaultLib.is_encrypted_file is deprecated.  Use vault.is_encrypted_file instead', version='2.4')
        return is_encrypted_file(file_obj)

    def encrypt(self, plaintext):
        """Vault encrypt a piece of data.

        :arg plaintext: a text or byte string to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.  The string
            contains a header identifying this as vault encrypted data and
            formatted to newline terminated lines of 80 characters.  This is
            suitable for dumping as is to a vault file.

        If the string passed in is a text string, it will be encoded to UTF-8
        before encryption.
        """
        b_plaintext = to_bytes(plaintext, errors='surrogate_or_strict')

        if is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        if not self.cipher_name or self.cipher_name not in CIPHER_WRITE_WHITELIST:
            self.cipher_name = u"AES256"

        try:
            this_cipher = CIPHER_MAPPING[self.cipher_name]()
        except KeyError:
            raise AnsibleError(u"{0} cipher could not be found".format(self.cipher_name))

        # encrypt data
        b_ciphertext = this_cipher.encrypt(b_plaintext, self.b_password)

        # format the data for output to the file
        b_vaulttext = self._format_output(b_ciphertext)
        return b_vaulttext

    def decrypt(self, vaulttext, filename=None):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data
        """
        b_vaulttext = to_bytes(vaulttext, errors='strict', encoding='utf-8')

        if self.b_password is None:
            raise AnsibleError("A vault password must be specified to decrypt data")

        if not is_encrypted(b_vaulttext):
            msg = "input is not vault encrypted data"
            if filename:
                msg += "%s is not a vault encrypted file" % filename
            raise AnsibleError(msg)

        # clean out header
        b_vaulttext = self._split_header(b_vaulttext)

        # create the cipher object
        if self.cipher_name in CIPHER_WHITELIST:
            this_cipher = CIPHER_MAPPING[self.cipher_name]()
        else:
            raise AnsibleError("{0} cipher could not be found".format(self.cipher_name))

        # try to unencrypt vaulttext
        b_plaintext = this_cipher.decrypt(b_vaulttext, self.b_password)
        if b_plaintext is None:
            msg = "Decryption failed"
            if filename:
                msg += " on %s" % filename
            raise AnsibleError(msg)

        return b_plaintext

    def _format_output(self, b_ciphertext):
        """ Add header and format to 80 columns

            :arg b_vaulttext: the encrypted and hexlified data as a byte string
            :returns: a byte str that should be dumped into a file.  It's
                formatted to 80 char columns and has the header prepended
        """

        if not self.cipher_name:
            raise AnsibleError("the cipher must be set before adding a header")

        header = b';'.join([b_HEADER, self.b_version,
                           to_bytes(self.cipher_name, 'utf-8', errors='strict')])
        b_vaulttext = [header]
        b_vaulttext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
        b_vaulttext += [b'']
        b_vaulttext = b'\n'.join(b_vaulttext)

        return b_vaulttext

    def _split_header(self, b_vaulttext):
        """Retrieve information about the Vault and clean the data

        When data is saved, it has a header prepended and is formatted into 80
        character lines.  This method extracts the information from the header
        and then removes the header and the inserted newlines.  The string returned
        is suitable for processing by the Cipher classes.

        :arg b_vaulttext: byte str containing the data from a save file
        :returns: a byte str suitable for passing to a Cipher class's
            decrypt() function.
        """
        # used by decrypt

        b_tmpdata = b_vaulttext.split(b'\n')
        b_tmpheader = b_tmpdata[0].strip().split(b';')

        self.b_version = b_tmpheader[1].strip()
        self.cipher_name = to_text(b_tmpheader[2].strip())
        b_ciphertext = b''.join(b_tmpdata[1:])

        return b_ciphertext


class VaultEditor:

    def __init__(self, b_password):
        self.vault = VaultLib(b_password)

    # TODO: mv shred file stuff to it's own class
    def _shred_file_custom(self, tmp_path):
        """"Destroy a file, when shred (core-utils) is not available

        Unix `shred' destroys files "so that they can be recovered only with great difficulty with
        specialised hardware, if at all". It is based on the method from the paper
        "Secure Deletion of Data from Magnetic and Solid-State Memory",
        Proceedings of the Sixth USENIX Security Symposium (San Jose, California, July 22-25, 1996).

        We do not go to that length to re-implement shred in Python; instead, overwriting with a block
        of random data should suffice.

        See https://github.com/ansible/ansible/pull/13700 .
        """

        file_len = os.path.getsize(tmp_path)

        if file_len > 0:  # avoid work when file was empty
            max_chunk_len = min(1024 * 1024 * 2, file_len)

            passes = 3
            with open(tmp_path, "wb") as fh:
                for _ in range(passes):
                    fh.seek(0, 0)
                    # get a random chunk of data, each pass with other length
                    chunk_len = random.randint(max_chunk_len // 2, max_chunk_len)
                    data = os.urandom(chunk_len)

                    for _ in range(0, file_len // chunk_len):
                        fh.write(data)
                    fh.write(data[:file_len % chunk_len])

                    assert(fh.tell() == file_len)  # FIXME remove this assert once we have unittests to check its accuracy
                    os.fsync(fh)

    def _shred_file(self, tmp_path):
        """Securely destroy a decrypted file

        Note standard limitations of GNU shred apply (For flash, overwriting would have no effect
        due to wear leveling; for other storage systems, the async kernel->filesystem->disk calls never
        guarantee data hits the disk; etc). Furthermore, if your tmp dirs is on tmpfs (ramdisks),
        it is a non-issue.

        Nevertheless, some form of overwriting the data (instead of just removing the fs index entry) is
        a good idea. If shred is not available (e.g. on windows, or no core-utils installed), fall back on
        a custom shredding method.
        """

        if not os.path.isfile(tmp_path):
            # file is already gone
            return

        try:
            r = call(['shred', tmp_path])
        except (OSError, ValueError):
            # shred is not available on this system, or some other error occurred.
            # ValueError caught because OS X El Capitan is raising an
            # exception big enough to hit a limit in python2-2.7.11 and below.
            # Symptom is ValueError: insecure pickle when shred is not
            # installed there.
            r = 1

        if r != 0:
            # we could not successfully execute unix shred; therefore, do custom shred.
            self._shred_file_custom(tmp_path)

        os.remove(tmp_path)

    def _edit_file_helper(self, filename, existing_data=None, force_save=False):

        # Create a tempfile
        fd, tmp_path = tempfile.mkstemp()
        os.close(fd)

        try:
            if existing_data:
                self.write_data(existing_data, tmp_path, shred=False)

            # drop the user into an editor on the tmp file
            call(self._editor_shell_command(tmp_path))
        except:
            # whatever happens, destroy the decrypted file
            self._shred_file(tmp_path)
            raise

        b_tmpdata = self.read_data(tmp_path)

        # Do nothing if the content has not changed
        if existing_data == b_tmpdata and not force_save:
            self._shred_file(tmp_path)
            return

        # encrypt new data and write out to tmp
        # An existing vaultfile will always be UTF-8,
        # so decode to unicode here
        b_ciphertext = self.vault.encrypt(b_tmpdata)
        self.write_data(b_ciphertext, tmp_path)

        # shuffle tmp file into place
        self.shuffle_files(tmp_path, filename)

    def _real_path(self, filename):
        # '-' is special to VaultEditor, dont expand it.
        if filename == '-':
            return filename

        real_path = os.path.realpath(filename)
        return real_path

    def encrypt_bytes(self, b_plaintext):

        b_ciphertext = self.vault.encrypt(b_plaintext)

        return b_ciphertext

    def encrypt_file(self, filename, output_file=None):

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.

        # follow the symlink
        filename = self._real_path(filename)

        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vault.encrypt(b_plaintext)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        # follow the symlink
        filename = self._real_path(filename)

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename):
        """ create a new encrypted file """

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleError("%s exists, please use 'edit' instead" % filename)

        self._edit_file_helper(filename)

    def edit_file(self, filename):

        # follow the symlink
        filename = self._real_path(filename)

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        if self.vault.cipher_name not in CIPHER_WRITE_WHITELIST:
            # we want to get rid of files encrypted with the AES cipher
            self._edit_file_helper(filename, existing_data=plaintext, force_save=True)
        else:
            self._edit_file_helper(filename, existing_data=plaintext, force_save=False)

    def plaintext(self, filename):

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        return plaintext

    def rekey_file(self, filename, b_new_password):

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        # This is more or less an assert, see #18247
        if b_new_password is None:
            raise AnsibleError('The value for the new_password to rekey %s with is not valid' % filename)

        new_vault = VaultLib(b_new_password)
        new_ciphertext = new_vault.encrypt(plaintext)

        self.write_data(new_ciphertext, filename)

        # preserve permissions
        os.chmod(filename, prev.st_mode)
        os.chown(filename, prev.st_uid, prev.st_gid)

    def read_data(self, filename):

        try:
            if filename == '-':
                data = sys.stdin.read()
            else:
                with open(filename, "rb") as fh:
                    data = fh.read()
        except Exception as e:
            raise AnsibleError(str(e))

        return data

    # TODO: add docstrings for arg types since this code is picky about that
    def write_data(self, data, filename, shred=True):
        """Write the data bytes to given path

        This is used to write a byte string to a file or stdout. It is used for
        writing the results of vault encryption or decryption. It is used for
        saving the ciphertext after encryption and it is also used for saving the
        plaintext after decrypting a vault. The type of the 'data' arg should be bytes,
        since in the plaintext case, the original contents can be of any text encoding
        or arbitrary binary data.

        When used to write the result of vault encryption, the val of the 'data' arg
        should be a utf-8 encoded byte string and not a text typ and not a text type..

        When used to write the result of vault decryption, the val of the 'data' arg
        should be a byte string and not a text type.

        :arg data: the byte string (bytes) data
        :arg filename: filename to save 'data' to.
        :arg shred: if shred==True, make sure that the original data is first shredded so that is cannot be recovered.
        :returns: None
        """
        # FIXME: do we need this now? data_bytes should always be a utf-8 byte string
        b_file_data = to_bytes(data, errors='strict')

        # get a ref to either sys.stdout.buffer for py3 or plain old sys.stdout for py2
        # We need sys.stdout.buffer on py3 so we can write bytes to it since the plaintext
        # of the vaulted object could be anything/binary/etc
        output = getattr(sys.stdout, 'buffer', sys.stdout)

        if filename == '-':
            output.write(b_file_data)
        else:
            if os.path.isfile(filename):
                if shred:
                    self._shred_file(filename)
                else:
                    os.remove(filename)
            with open(filename, "wb") as fh:
                fh.write(b_file_data)

    def shuffle_files(self, src, dest):
        prev = None
        # overwrite dest with src
        if os.path.isfile(dest):
            prev = os.stat(dest)
            # old file 'dest' was encrypted, no need to _shred_file
            os.remove(dest)
        shutil.move(src, dest)

        # reset permissions if needed
        if prev is not None:
            # TODO: selinux, ACLs, xattr?
            os.chmod(dest, prev.st_mode)
            os.chown(dest, prev.st_uid, prev.st_gid)

    def _editor_shell_command(self, filename):
        EDITOR = os.environ.get('EDITOR', 'vi')
        editor = shlex.split(EDITOR)
        editor.append(filename)

        return editor


########################################
#               CIPHERS                #
########################################

class VaultAES:

    # this version has been obsoleted by the VaultAES256 class
    # which uses encrypt-then-mac (fixing order) and also improving the KDF used
    # code remains for upgrade purposes only
    # http://stackoverflow.com/a/16761459

    # Note: strings in this class should be byte strings by default.

    def __init__(self):
        if not HAS_CRYPTOGRAPHY and not HAS_PYCRYPTO:
            raise AnsibleError(NEED_CRYPTO_LIBRARY)

    @staticmethod
    def _aes_derive_key_and_iv(b_password, b_salt, key_length, iv_length):

        """ Create a key and an initialization vector """

        b_d = b_di = b''
        while len(b_d) < key_length + iv_length:
            b_text = b''.join([b_di, b_password, b_salt])
            b_di = to_bytes(md5(b_text).digest(), errors='strict')
            b_d += b_di

        b_key = b_d[:key_length]
        b_iv = b_d[key_length:key_length + iv_length]

        return b_key, b_iv

    @staticmethod
    def encrypt(b_plaintext, b_password, key_length=32):

        """ Read plaintext data from in_file and write encrypted to out_file """

        raise AnsibleError("Encryption disabled for deprecated VaultAES class")

    @classmethod
    def _decrypt_cryptography(cls, b_salt, b_ciphertext, b_password, key_length):
        bs = algorithms.AES.block_size // 8
        b_key, b_iv = cls._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = C_Cipher(algorithms.AES(b_key), modes.CBC(b_iv), CRYPTOGRAPHY_BACKEND).decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        try:
            b_plaintext = unpadder.update(
                cipher.update(b_ciphertext) + cipher.finalize()
            ) + unpadder.finalize()
        except ValueError:
            # In VaultAES, ValueError: invalid padding bytes can mean bad
            # password was given
            raise AnsibleError("Decryption failed")

        # split out sha and verify decryption
        b_split_data = b_plaintext.split(b"\n", 1)
        b_this_sha = b_split_data[0]
        b_plaintext = b_split_data[1]
        b_test_sha = to_bytes(sha256(b_plaintext).hexdigest())

        if b_this_sha != b_test_sha:
            raise AnsibleError("Decryption failed")

        return b_plaintext

    @classmethod
    def _decrypt_pycrypto(cls, b_salt, b_ciphertext, b_password, key_length):
        in_file = BytesIO(b_ciphertext)
        in_file.seek(0)
        out_file = BytesIO()

        bs = AES_pycrypto.block_size
        b_key, b_iv = cls._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = AES_pycrypto.new(b_key, AES_pycrypto.MODE_CBC, b_iv)
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

    @classmethod
    def decrypt(cls, b_vaulttext, b_password, key_length=32):

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
        b_salt = b_vaultdata[len(b'Salted__'):16]
        b_ciphertext = b_vaultdata[16:]

        if HAS_CRYPTOGRAPHY:
            b_plaintext = cls._decrypt_cryptography(b_salt, b_ciphertext, b_password, key_length)
        elif HAS_PYCRYPTO:
            b_plaintext = cls._decrypt_pycrypto(b_salt, b_ciphertext, b_password, key_length)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + ' (Late detection)')

        return b_plaintext


class VaultAES256:

    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

    def __init__(self):
        if not HAS_CRYPTOGRAPHY and not HAS_PYCRYPTO:
            raise AnsibleError(NEED_CRYPTO_LIBRARY)

    @staticmethod
    def _create_key_cryptography(b_password, b_salt, key_length, iv_length):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * key_length + iv_length,
            salt=b_salt,
            iterations=10000,
            backend=CRYPTOGRAPHY_BACKEND)
        b_derivedkey = kdf.derive(b_password)

        return b_derivedkey

    @staticmethod
    def _pbkdf2_prf(p, s):
        hash_function = SHA256_pycrypto
        return HMAC_pycrypto.new(p, s, hash_function).digest()

    @classmethod
    def _create_key_pycrypto(cls, b_password, b_salt, key_length, iv_length):

        # make two keys and one iv

        b_derivedkey = PBKDF2_pycrypto(b_password, b_salt, dkLen=(2 * key_length) + iv_length,
                                       count=10000, prf=cls._pbkdf2_prf)
        return b_derivedkey

    @classmethod
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        key_length = 32

        if HAS_CRYPTOGRAPHY:
            # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
            iv_length = algorithms.AES.block_size // 8

            b_derivedkey = cls._create_key_cryptography(b_password, b_salt, key_length, iv_length)
            b_iv = b_derivedkey[(key_length * 2):(key_length * 2) + iv_length]
        elif HAS_PYCRYPTO:
            # match the size used for counter.new to avoid extra work
            iv_length = 16

            b_derivedkey = cls._create_key_pycrypto(b_password, b_salt, key_length, iv_length)
            b_iv = hexlify(b_derivedkey[(key_length * 2):(key_length * 2) + iv_length])
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in initctr)')

        b_key1 = b_derivedkey[:key_length]
        b_key2 = b_derivedkey[key_length:(key_length * 2)]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext, b_salt, b_key1, b_key2, b_iv):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return hexlify(b_hmac), hexlify(b_ciphertext)

    @staticmethod
    def _encrypt_pycrypto(b_plaintext, b_salt, b_key1, b_key2, b_iv):
        # PKCS#7 PAD DATA http://tools.ietf.org/html/rfc5652#section-6.3
        bs = AES_pycrypto.block_size
        padding_length = (bs - len(b_plaintext) % bs) or bs
        b_plaintext += to_bytes(padding_length * chr(padding_length), encoding='ascii', errors='strict')

        # COUNTER.new PARAMETERS
        # 1) nbits (integer) - Length of the counter, in bits.
        # 2) initial_value (integer) - initial value of the counter. "iv" from _gen_key_initctr

        ctr = Counter_pycrypto.new(128, initial_value=int(b_iv, 16))

        # AES.new PARAMETERS
        # 1) AES key, must be either 16, 24, or 32 bytes long -- "key" from _gen_key_initctr
        # 2) MODE_CTR, is the recommended mode
        # 3) counter=<CounterObject>

        cipher = AES_pycrypto.new(b_key1, AES_pycrypto.MODE_CTR, counter=ctr)

        # ENCRYPT PADDED DATA
        b_ciphertext = cipher.encrypt(b_plaintext)

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC_pycrypto.new(b_key2, b_ciphertext, SHA256_pycrypto)

        return to_bytes(hmac.hexdigest(), errors='surrogate_or_strict'), hexlify(b_ciphertext)

    @classmethod
    def encrypt(cls, b_plaintext, b_password):
        b_salt = os.urandom(32)
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_salt, b_key1, b_key2, b_iv)
        elif HAS_PYCRYPTO:
            b_hmac, b_ciphertext = cls._encrypt_pycrypto(b_plaintext, b_salt, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in encrypt)')

        b_vaulttext = b'\n'.join([hexlify(b_salt), b_hmac, b_ciphertext])
        # Unnecessary but getting rid of it is a backwards incompatible vault
        # format change
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    @staticmethod
    def _decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(unhexlify(b_crypted_hmac))
        except InvalidSignature:
            return None

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(
            decryptor.update(b_ciphertext) + decryptor.finalize()
        ) + unpadder.finalize()

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

    @classmethod
    def _decrypt_pycrypto(cls, b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac_decrypt = HMAC_pycrypto.new(b_key2, b_ciphertext, SHA256_pycrypto)
        if not cls._is_equal(b_crypted_hmac, to_bytes(hmac_decrypt.hexdigest())):
            return None

        # SET THE COUNTER AND THE CIPHER
        ctr = Counter_pycrypto.new(128, initial_value=int(b_iv, 16))
        cipher = AES_pycrypto.new(b_key1, AES_pycrypto.MODE_CTR, counter=ctr)

        # DECRYPT PADDED DATA
        b_plaintext = cipher.decrypt(b_ciphertext)

        # UNPAD DATA
        if PY3:
            padding_length = b_plaintext[-1]
        else:
            padding_length = ord(b_plaintext[-1])

        b_plaintext = b_plaintext[:-padding_length]
        return b_plaintext

    @classmethod
    def decrypt(cls, b_vaulttext, b_password):
        # SPLIT SALT, DIGEST, AND DATA
        b_vaulttext = unhexlify(b_vaulttext)
        b_salt, b_crypted_hmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
        b_salt = unhexlify(b_salt)
        b_ciphertext = unhexlify(b_ciphertext)
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_plaintext = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
        elif HAS_PYCRYPTO:
            b_plaintext = cls._decrypt_pycrypto(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in decrypt)')

        return b_plaintext

# Keys could be made bytes later if the code that gets the data is more
# naturally byte-oriented
CIPHER_MAPPING = {
    u'AES': VaultAES,
    u'AES256': VaultAES256,
}
