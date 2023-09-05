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

import errno
import fcntl
import os
import random
import shlex
import shutil
import subprocess
import sys
import tempfile

from ansible import constants as C
from ansible.errors import AnsibleAssertionError, AnsibleError, AnsibleVaultError
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe
from .ciphers import CIPHER_WRITE_WHITELIST
from .lib import VaultLib
from .util import parse_vaulttext_envelope

display = Display()


class VaultEditor:

    def __init__(self, vault=None):
        # TODO: it may be more useful to just make VaultSecrets and index of VaultLib objects...
        self.vault = vault or VaultLib()

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
                for i in range(passes):
                    fh.seek(0, 0)
                    # get a random chunk of data, each pass with other length
                    chunk_len = random.randint(max_chunk_len // 2, max_chunk_len)
                    data = os.urandom(chunk_len)

                    for j in range(0, file_len // chunk_len):
                        fh.write(data)
                    fh.write(data[:file_len % chunk_len])

                    # FIXME remove this assert once we have unittests to check its accuracy
                    if fh.tell() != file_len:
                        raise AnsibleAssertionError()

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
            r = subprocess.call(['shred', tmp_path])
        except (OSError, ValueError):
            # shred is not available on this system, or some other error occurred.
            # ValueError caught because macOS El Capitan is raising an
            # exception big enough to hit a limit in python2-2.7.11 and below.
            # Symptom is ValueError: insecure pickle when shred is not
            # installed there.
            r = 1

        if r != 0:
            # we could not successfully execute unix shred; therefore, do custom shred.
            self._shred_file_custom(tmp_path)

        os.remove(tmp_path)

    def _edit_file_helper(self, filename, secret, existing_data=None, force_save=False, vault_id=None):

        # Create a tempfile
        root, ext = os.path.splitext(os.path.realpath(filename))
        fd, tmp_path = tempfile.mkstemp(suffix=ext, dir=C.DEFAULT_LOCAL_TMP)

        cmd = self._editor_shell_command(tmp_path)
        try:
            if existing_data:
                self.write_data(existing_data, fd, shred=False)
        except Exception:
            # if an error happens, destroy the decrypted file
            self._shred_file(tmp_path)
            raise
        finally:
            os.close(fd)

        try:
            # drop the user into an editor on the tmp file
            subprocess.call(cmd)
        except Exception as e:
            # if an error happens, destroy the decrypted file
            self._shred_file(tmp_path)
            raise AnsibleError(f'Unable to execute the command "{" ".join(cmd)}": {e}') from e

        b_tmpdata = self.read_data(tmp_path)

        # Do nothing if the content has not changed
        if force_save or existing_data != b_tmpdata:

            # encrypt new data and write out to tmp
            # An existing vaultfile will always be UTF-8,
            # so decode to unicode here
            b_ciphertext = self.vault.encrypt(b_tmpdata, secret, vault_id=vault_id)
            self.write_data(b_ciphertext, tmp_path)

            # shuffle tmp file into place
            self.shuffle_files(tmp_path, filename)
            display.vvvvv(f'Saved edited file "{to_text(filename)}" encrypted using {to_text(secret)} '
                          f'and vault id "{to_text(vault_id)}"')

        # always shred temp, jic
        self._shred_file(tmp_path)

    def _real_path(self, filename):
        # '-' is special to VaultEditor, dont expand it.
        if filename == '-':
            return filename

        real_path = os.path.realpath(filename)
        return real_path

    def encrypt_bytes(self, b_plaintext, secret, vault_id=None):
        return self.vault.encrypt(b_plaintext, secret, vault_id=vault_id)

    def encrypt_file(self, filename, secret, vault_id=None, output_file=None):

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.

        # follow the symlink
        filename = self._real_path(filename)

        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vault.encrypt(b_plaintext, secret, vault_id=vault_id)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        # follow the symlink
        filename = self._real_path(filename)

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault.decrypt(ciphertext, filename=filename)
        except AnsibleError as e:
            raise AnsibleError(f"{e} for {to_native(filename)}") from e
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename, secret, vault_id=None):
        """ create a new encrypted file """

        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            display.warning(f"{to_text(dirname)} does not exist, creating...")
            makedirs_safe(dirname)

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleError(f"{filename} exists, please use 'edit' instead")

        self._edit_file_helper(filename, secret, vault_id=vault_id)

    def edit_file(self, filename):
        vault_id_used = None
        vault_secret_used = None
        # follow the symlink
        filename = self._real_path(filename)

        b_vaulttext = self.read_data(filename)

        # vault or yaml files are always utf8
        vaulttext = to_text(b_vaulttext)

        try:
            # vaulttext gets converted back to bytes, but alas
            # TODO: return the vault_id that worked?
            plaintext, vault_id_used, vault_secret_used = self.vault.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError(f"{e} for {to_native(filename)}") from e

        # Figure out the vault id from the file, to select the right secret to re-encrypt it
        # (duplicates parts of decrypt, but alas...)
        dummy, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext, filename=filename)

        # vault id here may not be the vault id actually used for decrypting
        # as when the edited file has no vault-id but is decrypted by non-default id in secrets
        # (vault_id=default, while a different vault-id decrypted)

        # we want to get rid of files encrypted with the AES cipher
        force_save = (cipher_name not in CIPHER_WRITE_WHITELIST)

        # Keep the same vault-id (and version) as in the header
        self._edit_file_helper(filename, vault_secret_used, existing_data=plaintext, force_save=force_save, vault_id=vault_id)

    def plaintext(self, filename):

        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        try:
            plaintext = self.vault.decrypt(vaulttext, filename=filename)
            return plaintext
        except AnsibleError as e:
            raise AnsibleVaultError(f"{e} for {to_native(filename)}") from e

    # FIXME/TODO: make this use VaultSecret
    def rekey_file(self, filename, new_vault_secret, new_vault_id=None):

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        display.vvvvv(f'Rekeying file "{to_text(filename)}" to with new vault-id "{to_text(new_vault_id)}" '
                      f'and vault secret {to_text(new_vault_secret)}')
        try:
            plaintext, vault_id_used, _dummy = self.vault.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError(f"{e} for {to_native(filename)}") from e

        # This is more or less an assert, see #18247
        if new_vault_secret is None:
            raise AnsibleError(f'The value for the new_password to rekey {filename} with is not valid')

        # FIXME: VaultContext...?  could rekey to a different vault_id in the same VaultSecrets

        # Need a new VaultLib because the new vault data can be a different
        # vault lib format or cipher (for ex, when we migrate 1.0 style vault data to
        # 1.1 style data we change the version and the cipher). This is where a VaultContext might help

        # the new vault will only be used for encrypting, so it doesn't need the vault secrets
        # (we will pass one in directly to encrypt)
        new_vault = VaultLib(secrets={})
        b_new_vaulttext = new_vault.encrypt(plaintext, new_vault_secret, vault_id=new_vault_id)

        self.write_data(b_new_vaulttext, filename)

        # preserve permissions
        os.chmod(filename, prev.st_mode)
        os.chown(filename, prev.st_uid, prev.st_gid)

        display.vvvvv(
            f'Rekeyed file "{to_text(filename)}" (decrypted with vault id "{to_text(vault_id_used)}") was encrypted '
            f'with new vault-id "{to_text(new_vault_id)}" and vault secret {to_text(new_vault_secret)}')

    def read_data(self, filename):

        try:
            if filename == '-':
                data = sys.stdin.buffer.read()
            else:
                with open(filename, "rb") as fh:
                    data = fh.read()
        except Exception as e:
            msg = to_native(e)
            if not msg:
                msg = repr(e)
            raise AnsibleError(f'Unable to read source file ({to_native(filename)}): {msg}')

        return data

    def write_data(self, data, thefile, shred=True, mode=0o600):
        # TODO: add docstrings for arg types since this code is picky about that
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
        :arg thefile: file descriptor or filename to save 'data' to.
        :arg shred: if shred==True, make sure that the original data is first shredded so that is cannot be recovered.
        :returns: None
        """
        # FIXME: do we need this now? data_bytes should always be a utf-8 byte string
        b_file_data = to_bytes(data, errors='strict')

        # check if we have a file descriptor instead of a path
        is_fd = False
        try:
            is_fd = (isinstance(thefile, int) and fcntl.fcntl(thefile, fcntl.F_GETFD) != -1)
        except Exception:
            pass

        if is_fd:
            # if passed descriptor, use that to ensure secure access, otherwise it is a string.
            # assumes the fd is securely opened by caller (mkstemp)
            os.ftruncate(thefile, 0)
            os.write(thefile, b_file_data)
        elif thefile == '-':
            # get a ref to either sys.stdout.buffer for py3 or plain old sys.stdout for py2
            # We need sys.stdout.buffer on py3 so we can write bytes to it since the plaintext
            # of the vaulted object could be anything/binary/etc
            output = getattr(sys.stdout, 'buffer', sys.stdout)
            output.write(b_file_data)
        else:
            # file names are insecure and prone to race conditions, so remove and create securely
            if os.path.isfile(thefile):
                if shred:
                    self._shred_file(thefile)
                else:
                    os.remove(thefile)

            # when setting new umask, we get previous as return
            current_umask = os.umask(0o077)
            try:
                try:
                    # create file with secure permissions
                    fd = os.open(thefile, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_TRUNC, mode)
                except OSError as ose:
                    # Want to catch FileExistsError, which doesn't exist in Python 2, so catch OSError
                    # and compare the error number to get equivalent behavior in Python 2/3
                    if ose.errno == errno.EEXIST:
                        raise AnsibleError('Vault file got recreated while we were operating on it: %s' % to_native(ose))

                    raise AnsibleError('Problem creating temporary vault file: %s' % to_native(ose))

                try:
                    # now write to the file and ensure ours is only data in it
                    os.ftruncate(fd, 0)
                    os.write(fd, b_file_data)
                except OSError as e:
                    raise AnsibleError('Unable to write to temporary vault file: %s' % to_native(e))
                finally:
                    # Make sure the file descriptor is always closed and reset umask
                    os.close(fd)
            finally:
                os.umask(current_umask)

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
        env_editor = C.config.get_config_value('EDITOR')
        editor = shlex.split(env_editor)
        editor.append(filename)

        return editor
