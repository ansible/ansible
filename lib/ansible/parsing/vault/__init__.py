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

import os
import shlex
import shutil
import sys
import tempfile
import random
from subprocess import call
from hashlib import sha256
from binascii import hexlify
from binascii import unhexlify
from hashlib import md5

# Note: Only used for loading obsolete VaultAES files.  All files are written
# using the newer VaultAES256 which does not require md5

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import (
    Cipher as C_Cipher, algorithms, modes
)

from ansible.compat.six import PY3, binary_type
from ansible.compat.six.moves import zip
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


BACKEND = default_backend()
b_HEADER = b'$ANSIBLE_VAULT'
CIPHER_WHITELIST = frozenset((u'AES', u'AES256'))
CIPHER_WRITE_WHITELIST = frozenset((u'AES256',))
# See also CIPHER_MAPPING at the bottom of the file which maps cipher strings
# (used in VaultFile header) to a cipher class


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
        vaulttext = file_obj.read(count)
        try:
            b_vaulttext = to_bytes(to_text(vaulttext, encoding='ascii', errors='strict'), encoding='ascii', errors='strict')
        except (UnicodeError, TypeError):
            # At present, vault files contain only ascii characters.  The encoding is utf-8
            # without BOM (for future expansion).  If the header does not
            # decode as ascii then we know we do not have proper vault
            # encrypted data.
            return False
    finally:
        file_obj.seek(current_position)

    return is_encrypted(b_vaulttext)


class VaultLib:

    def __init__(self, password):
        self.b_password = to_bytes(password, errors='strict', encoding='utf-8')
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
            Cipher = CIPHER_MAPPING[self.cipher_name]
        except KeyError:
            raise AnsibleError(u"{0} cipher could not be found".format(self.cipher_name))
        this_cipher = Cipher()

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
        cipher_class_name = u'Vault{0}'.format(self.cipher_name)

        if cipher_class_name in globals() and self.cipher_name in CIPHER_WHITELIST:
            Cipher = globals()[cipher_class_name]
            this_cipher = Cipher()
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
                        to_bytes(self.cipher_name,'utf-8', errors='strict')])
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

    def __init__(self, password):
        self.vault = VaultLib(password)

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
            max_chunk_len = min(1024*1024*2, file_len)

            passes = 3
            with open(tmp_path,  "wb") as fh:
                for _ in range(passes):
                    fh.seek(0,  0)
                    # get a random chunk of data, each pass with other length
                    chunk_len = random.randint(max_chunk_len//2, max_chunk_len)
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
        _, tmp_path = tempfile.mkstemp()

        if existing_data:
            self.write_data(existing_data, tmp_path, shred=False)

        # drop the user into an editor on the tmp file
        try:
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

    def encrypt_file(self, filename, output_file=None):

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.
        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vault.encrypt(b_plaintext)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        ciphertext = self.read_data(filename)
        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e),to_bytes(filename)))
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename):
        """ create a new encrypted file """

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleError("%s exists, please use 'edit' instead" % filename)

        self._edit_file_helper(filename)

    def edit_file(self, filename):

        ciphertext = self.read_data(filename)
        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e),to_bytes(filename)))

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
            raise AnsibleError("%s for %s" % (to_bytes(e),to_bytes(filename)))

        return plaintext

    def rekey_file(self, filename, new_password):

        prev = os.stat(filename)
        ciphertext = self.read_data(filename)
        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e),to_bytes(filename)))

        # This is more or less an assert, see #18247
        if new_password is None:
            raise AnsibleError('The value for the new_password to rekey %s with is not valid' % filename)

        new_vault = VaultLib(new_password)
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
        """write data to given path

        :arg data: the encrypted and hexlified data as a utf-8 byte string
        :arg filename: filename to save 'data' to.
        :arg shred: if shred==True, make sure that the original data is first shredded so
        that is cannot be recovered.
        """
        # FIXME: do we need this now? data_bytes should always be a utf-8 byte string
        b_file_data = to_bytes(data, errors='strict')

        if filename == '-':
            sys.stdout.write(b_file_data)
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
        EDITOR = os.environ.get('EDITOR','vi')
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

    def _aes_derive_key_and_iv(self, b_password, b_salt, key_length, iv_length):

        """ Create a key and an initialization vector """

        b_d = b_di = b''
        while len(b_d) < key_length + iv_length:
            b_text = b''.join([b_di, b_password, b_salt])
            b_di = to_bytes(md5(b_text).digest(), errors='strict')
            b_d += b_di

        b_key = b_d[:key_length]
        b_iv = b_d[key_length:key_length+iv_length]

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

        display.deprecated(u'The VaultAES format is insecure and has been'
                ' deprecated since Ansible-1.5.  Use vault rekey FILENAME to'
                ' switch to the newer VaultAES256 format', version='2.3')
        # http://stackoverflow.com/a/14989032

        b_vaultdata = unhexlify(b_vaulttext)
        b_tmpsalt = b_vaultdata[:16]
        b_ciphertext = b_vaultdata[16:]

        bs = algorithms.AES.block_size // 8
        b_salt = b_tmpsalt[len(b'Salted__'):]
        b_key, b_iv = self._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = C_Cipher(algorithms.AES(b_key), modes.CBC(b_iv), BACKEND).decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        b_plaintext = unpadder.update(
            cipher.update(b_ciphertext) + cipher.finalize()
        ) + unpadder.finalize()

        # split out sha and verify decryption
        b_split_data = b_plaintext.split(b"\n", 1)
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

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

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


# Keys could be made bytes later if the code that gets the data is more
# naturally byte-oriented
CIPHER_MAPPING = {
    u'AES': VaultAES,
    u'AES256': VaultAES256,
}
