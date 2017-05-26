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

from ansible.errors import AnsibleError, AnsibleVaultError
from ansible.parsing.vault.cipher_loader import CIPHER_MAPPING, CIPHER_ENCRYPT_WHITELIST, get_decrypt_cipher, get_encrypt_cipher
from ansible.parsing.vault import envelope

from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def is_encrypted(data):
    """ Test if this is vault encrypted data blob

    :arg data: a byte or text string to test whether it is recognized as vault
        encrypted data
    :returns: True if it is recognized.  Otherwise, False.
    """
    return envelope.is_vault_envelope(data)


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

    # The prereqs can be different for each cipher impl
    def _check_prereqs(self):
        default_cipher_class = CIPHER_MAPPING[self.default_cipher_name]
        return default_cipher_class.check_prereqs()

    def __init__(self, b_password):
        self.b_password = to_bytes(b_password, errors='strict', encoding='utf-8')
        self.default_cipher_name = 'AES256'
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
            raise AnsibleVaultError("input is already encrypted")

        # use the default cipher
        cipher_class = get_encrypt_cipher(self.default_cipher_name)
        cipher = cipher_class()

        # encrypt data
        b_ciphertext = cipher.encrypt(b_plaintext, self.b_password)

        # format the data for output to the file
        b_vaulttext = envelope.format_envelope(b_ciphertext, cipher.name, self.b_version)
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
            raise AnsibleVaultError("A vault password must be specified to decrypt data")

        try:
            b_ciphertext, cipher_name, b_version = envelope.parse_envelope(b_vaulttext)
            return self.decrypt_ciphertext(b_ciphertext, cipher_name, b_version)
        except AnsibleVaultError as e:
            if filename:
                msg = "%s for filename %s" % (e, filename)
                raise AnsibleVaultError(msg)
            raise

    def decrypt_ciphertext(self, b_ciphertext, cipher_name, b_version):

        cipher_class = get_decrypt_cipher(cipher_name)
        cipher = cipher_class()

        # try to unencrypt vaulttext
        b_plaintext = cipher.decrypt(b_ciphertext, self.b_password)
        if b_plaintext is None:
            msg = "Decryption failed"
            raise AnsibleVaultError(msg)

        return b_plaintext


class VaultEditor:

    def __init__(self, b_password):
        self.vault = VaultLib(b_password)

    def _check_prereqs(self):
        return self.vault._check_prereqs()

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
        self._check_prereqs()

        b_ciphertext = self.vault.encrypt(b_plaintext)

        return b_ciphertext

    def encrypt_file(self, filename, output_file=None):

        self._check_prereqs()

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.

        # follow the symlink
        filename = self._real_path(filename)

        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vault.encrypt(b_plaintext)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        self._check_prereqs()

        # follow the symlink
        filename = self._real_path(filename)

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_bytes(e), to_bytes(filename)))
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename):
        """ create a new encrypted file """

        self._check_prereqs()

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleVaultError("%s exists, please use 'edit' instead" % filename)

        self._edit_file_helper(filename)

    def edit_file(self, filename):

        self._check_prereqs()

        # follow the symlink
        filename = self._real_path(filename)

        vaulttext = self.read_data(filename)

        try:
            b_ciphertext, cipher_name, b_version = envelope.parse_envelope(vaulttext)
            plaintext = self.vault.decrypt_ciphertext(b_ciphertext, cipher_name, b_version)
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        if cipher_name not in CIPHER_ENCRYPT_WHITELIST:
            # we want to get rid of files encrypted with the AES cipher
            self._edit_file_helper(filename, existing_data=plaintext, force_save=True)
        else:
            self._edit_file_helper(filename, existing_data=plaintext, force_save=False)

    def plaintext(self, filename):

        self._check_prereqs()
        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        return plaintext

    def rekey_file(self, filename, b_new_password):

        self._check_prereqs()

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext)
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        # This is more or less an assert, see #18247
        if b_new_password is None:
            raise AnsibleVaultError('The value for the new_password to rekey %s with is not valid' % filename)

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
            raise AnsibleVaultError(str(e))

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
