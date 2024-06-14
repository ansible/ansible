# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import errno
import fcntl
import os
import random
import shlex
import shutil
import subprocess
import sys
import tempfile

import typing as t

import ansible.parsing.vault.ciphers as CI

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError, AnsibleVaultError, AnsibleVaultFormatError
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.parsing.vault import Vault, is_encrypted, format_vaulttext_envelope, parse_vaulttext_envelope
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe

display = Display()

# TODO: use function to match
CIPHER_MAPPING = {
    'AES256': CI.VaultAES256,
    'AES256v2': CI.VaultAES256v2,
}


def match_secrets(secrets: list[str], target_vault_ids: list[str]) -> list[str]:
    '''Find all VaultSecret objects that are mapped to any of the target_vault_ids in secrets'''
    if not secrets:
        return []

    matches = [(vault_id, secret) for vault_id, secret in secrets if vault_id in target_vault_ids]
    return matches


def match_best_secret(secrets: list[str], target_vault_ids: list[str]) -> str | None:
    '''Find the best secret from secrets that matches target_vault_ids

    Since secrets should be ordered so the early secrets are 'better' than later ones, this
    just finds all the matches, then returns the first secret'''
    matches = match_secrets(secrets, target_vault_ids)
    if matches:
        return matches[0]
    # raise exception?
    return None


def match_encrypt_vault_id_secret(secrets: list[str], encrypt_vault_id: str | None = None):
    # See if the --encrypt-vault-id matches a vault-id
    display.vvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))

    if encrypt_vault_id is None:
        raise AnsibleError('match_encrypt_vault_id_secret requires a non None encrypt_vault_id')

    encrypt_vault_id_matchers = [encrypt_vault_id]
    encrypt_secret = match_best_secret(secrets, encrypt_vault_id_matchers)

    # return the best match for --encrypt-vault-id
    if encrypt_secret:
        return encrypt_secret

    # If we specified a encrypt_vault_id and we couldn't find it, dont
    # fallback to using the first/best secret
    raise AnsibleVaultError('Did not find a match for --encrypt-vault-id=%s in the known vault-ids %s' % (encrypt_vault_id,
                                                                                                          [_v for _v, _vs in secrets]))


def match_encrypt_secret(secrets: list[str], encrypt_vault_id: str | None = None):
    '''Find the best/first/only secret in secrets to use for encrypting'''

    display.vvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))
    # See if the --encrypt-vault-id matches a vault-id
    if encrypt_vault_id:
        return match_encrypt_vault_id_secret(secrets, encrypt_vault_id=encrypt_vault_id)

    # Find the best/first secret from secrets since we didnt specify otherwise
    # ie, consider all of the available secrets as matches
    _vault_id_matchers = [_vault_id for _vault_id, dummy in secrets]
    best_secret = match_best_secret(secrets, _vault_id_matchers)

    # can be empty list sans any tuple
    return best_secret


class VaultLib:
    def __init__(self, secrets: str | None = None):
        self.secrets = secrets or []
        self.cipher_name = None
        self.default_version = '1.3'

    @staticmethod
    def is_encrypted(vaulttext: t.AnyStr):
        return is_encrypted(vaulttext)

    def encrypt(self, vault: Vault, secret: str | None = None):
        """Vault encrypt a piece of data.

        :arg vault: A vault object that has plaintext in it's "raw" property to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.  The string
            contains a header identifying this as vault encrypted data and
            formatted to newline terminated lines of 80 characters.  This is
            suitable for dumping as is to a vault file.

        If the string passed in is a text string, it will be encoded to UTF-8
        before encryption.
        """

        if secret is None:
            if self.secrets:
                dummy, secret = match_encrypt_secret(self.secrets)
            else:
                raise AnsibleVaultError("A vault password must be specified to encrypt data")

        b_plaintext = bytes(vault.raw)

        if is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        try:
            this_cipher = CIPHER_MAPPING[vault.cipher]()
        except KeyError:
            raise AnsibleError(f"Requested '{vault.cipher}' cipher could not be found")

        # encrypt data
        if vault.vault_id:
            display.vvvvv(f'Encrypting with vault_id "{vault.vault_id}"')
        else:
            display.vvvvv('Encrypting without a vault_id using')

        b_ciphertext = this_cipher.encrypt(b_plaintext, secret, vault.salt)

        # format the data for output to the file
        b_vaulttext = format_vaulttext_envelope(b_ciphertext,
                                                vault.cipher,
                                                vault_id=vault.vault_id)
        return b_vaulttext

    def decrypt(self, vaulttext: str, filename: str | None = None, obj: object | None = None):
        '''Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id that was used

        '''
        plaintext, vault_id, vault_secret = self.decrypt_and_get_vault_id(vaulttext, filename=filename, obj=obj)
        return plaintext

    def decrypt_and_get_vault_id(self, vaulttext: str, filename: str | None = None, obj: object | None = None):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id vault-secret that was used

        """
        b_vaulttext = to_bytes(vaulttext, errors='strict', encoding='utf-8')

        if self.secrets is None:
            msg = "A vault password must be specified to decrypt data"
            if filename:
                msg += " in file %s" % to_native(filename)
            raise AnsibleVaultError(msg)

        if not is_encrypted(b_vaulttext):
            msg = "input is not vault encrypted data. "
            if filename:
                msg += "%s is not a vault encrypted file" % to_native(filename)
            raise AnsibleError(msg)

        vault = parse_vaulttext_envelope(b_vaulttext, filename=filename)

        return self._open_vault(vault, obj)

    def _open_vault(self, vault: Vault, obj: object):

        # create the cipher object, note that the cipher used for decrypt can
        # be different than the cipher used for encrypt
        if vault.cipher in vault.CIPHER_ALLOWLIST:
            this_cipher = CIPHER_MAPPING[vault.cipher]()
        else:
            raise AnsibleError("{0} cipher could not be found".format(vault.cipher))

        b_plaintext = None

        if not self.secrets:
            raise AnsibleVaultError('Attempting to decrypt but no vault secrets found')

        # WARNING: Currently, the vault id is not required to match the vault id in the vault blob to
        #          decrypt a vault properly. The vault id in the vault blob is not part of the encrypted
        #          or signed vault payload. There is no cryptographic checking/verification/validation of the
        #          vault blobs vault id. It can be tampered with and changed. The vault id is just a nick
        #          name to use to pick the best secret and provide some ux/ui info.

        # iterate over all the applicable secrets (all of them by default) until one works...
        # if we specify a vault_id, only the corresponding vault secret is checked and
        # we check it first.

        vault_id_matchers = []
        vault_id_used = None
        vault_secret_used = None

        if vault.vault_id:
            display.vvvvv(f'Found a vault_id ({vault.vault_id}) in the vaulttext')
            vault_id_matchers.append(vault.vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv(f'We have a secret associated with vault id (vault.vault_id), will try to use to decrypt: {vaultfilename}')
            else:
                display.vvvvv(f'Found a vault_id (vault.vault_id) in the vault text, but we do not have a associated secret (--vault-id)')

        # Not adding the other secrets to vault_secret_ids enforces a match between the vault_id from the vault_text and
        # the known vault secrets.
        if not C.DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault.vault_id])

        matched_secrets = match_secrets(self.secrets, vault_id_matchers)

        # for vault_secret_id in vault_secret_ids:
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv(f'Trying to use matched vault secret id={vault.vault_id} to decrypt: {vault.filename}')

            try:
                # secret = self.secrets[vault_secret_id]
                display.vvvv(f'Trying matched secret for vault_id={vault.vault_id}')
                b_plaintext = this_cipher.decrypt(vault.raw, vault_secret)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    file_slug = ''
                    if vault.filename:
                        file_slug = ' of "%s"' % vault.filename
                    display.vvvvv(f'Decrypt successful for vault_id={vault.vault_id}')
                    break
            except AnsibleVaultFormatError as exc:
                exc.obj = obj
                exc.filename = vault.filename
                raise exc
            except AnsibleError as e:
                display.vvvv(f'Tried to use the vault secret (id={vault.vault_id}) to decrypt ({vault.filename}) but it failed: {e}')
                continue
        else:
            raise AnsibleVaultError("Decryption failed (no vault secrets were found that could decrypt)", filename=vault.filename)

        if b_plaintext is None:
            raise AnsibleVaultError("Decryption failed, no data retrieved", filename=vault.filename)

        return b_plaintext, vault_id_used, vault_secret_used


class VaultEditor:

    def __init__(self, vault_mgr: VaultLib | None = None):
        # TODO: it may be more useful to just make VaultSecrets and index of VaultLib objects...
        self.vault_mgr = vault_mgr or VaultLib()

    # TODO: mv shred file stuff to it's own class
    def _shred_file_custom(self, tmp_path: bytes):
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
                for dummy in range(passes):
                    fh.seek(0, 0)
                    # get a random chunk of data, each pass with other length
                    chunk_len = random.randint(max_chunk_len // 2, max_chunk_len)
                    data = os.urandom(chunk_len)

                    for dummy in range(0, file_len // chunk_len):
                        fh.write(data)
                    fh.write(data[:file_len % chunk_len])

                    # FIXME remove this assert once we have unittests to check its accuracy
                    if fh.tell() != file_len:
                        raise AnsibleAssertionError()

                    os.fsync(fh)

    def _shred_file(self, tmp_path: bytes):
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
            raise AnsibleError('Unable to execute the command "%s": %s' % (' '.join(cmd), to_native(e)))

        b_tmpdata = self.read_data(tmp_path)

        # Do nothing if the content has not changed
        if force_save or existing_data != b_tmpdata:

            # encrypt new data and write out to tmp
            # An existing vaultfile will always be UTF-8,
            # so decode to unicode here
            b_ciphertext = self.vault_mgr.encrypt(b_tmpdata, secret, vault_id=vault_id)
            self.write_data(b_ciphertext, tmp_path)

            # shuffle tmp file into place
            self.shuffle_files(tmp_path, filename)
            display.vvvvv(u'Saved edited file "%s" encrypted using %s and  vault id "%s"' % (to_text(filename), to_text(secret), to_text(vault_id)))

        # always shred temp, jic
        self._shred_file(tmp_path)

    def _real_path(self, filename: str):
        # '-' is special to VaultEditor, dont expand it.
        if filename == '-':
            return filename

        real_path = os.path.realpath(filename)
        return real_path

    def encrypt_bytes(self, b_plaintext: bytes, secret: str, vault_id: str | None = None):

        b_ciphertext = self.vault_mgr.encrypt(b_plaintext, secret, vault_id=vault_id)

        return b_ciphertext

    def encrypt_file(self, filename: str, secret: str, vault_id: str | None = None, output_file: str | None = None):

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.

        # follow the symlink
        filename = self._real_path(filename)

        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vault_mgr.encrypt(b_plaintext, secret, vault_id=vault_id)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename: str, output_file: str | None = None):

        # follow the symlink
        filename = self._real_path(filename)

        ciphertext = self.read_data(filename)

        try:
            plaintext = self.vault_mgr.decrypt(ciphertext, filename=filename)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_native(e), to_native(filename)))
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename: str, secret: str, vault_id: str | None = None):
        """ create a new encrypted file """

        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            display.warning(u"%s does not exist, creating..." % to_text(dirname))
            makedirs_safe(dirname)

        # FIXME: If we can raise an error here, we can probably just make it
        # behave like edit instead.
        if os.path.isfile(filename):
            raise AnsibleError("%s exists, please use 'edit' instead" % filename)

        self._edit_file_helper(filename, secret, vault_id=vault_id)

    def edit_file(self, filename: str):
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
            plaintext, vault_id_used, vault_secret_used = self.vault_mgr.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_native(e), to_native(filename)))

        # Figure out the vault id from the file, to select the right secret to re-encrypt it
        # (duplicates parts of decrypt, but alas...)
        vault = parse_vaulttext_envelope(b_vaulttext, filename=filename)

        # vault id here may not be the vault id actually used for decrypting
        # as when the edited file has no vault-id but is decrypted by non-default id in secrets
        # (vault_id=default, while a different vault-id decrypted)

        # we want to get rid of files encrypted with the AES cipher
        force_save = (vault.cipher not in vault.CIPHER_WRITE_ALLOWLIST)

        # Keep the same vault-id (and version) as in the header
        self._edit_file_helper(filename, vault_secret_used, existing_data=plaintext, force_save=force_save, vault_id=vault.vault_id)

    def plaintext(self, filename: str):

        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        try:
            plaintext = self.vault_mgr.decrypt(vaulttext, filename=filename)
            return plaintext
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_native(e), to_native(filename)))

    # FIXME/TODO: make this use VaultSecret
    def rekey_file(self, filename: str, new_vault_secret: str, new_vault_id: str | None = None):

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        display.vvvvv(u'Rekeying file "%s" to with new vault-id "%s" and vault secret %s' %
                      (to_text(filename), to_text(new_vault_id), to_text(new_vault_secret)))
        try:
            plaintext, vault_id_used, _dummy = self.vault_mgr.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_native(e), to_native(filename)))

        # This is more or less an assert, see #18247
        if new_vault_secret is None:
            raise AnsibleError('The value for the new_password to rekey %s with is not valid' % filename)

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

        display.vvvvv(u'Rekeyed file "%s" (decrypted with vault id "%s") was encrypted with new vault-id "%s" and vault secret %s' %
                      (to_text(filename), to_text(vault_id_used), to_text(new_vault_id), to_text(new_vault_secret)))

    def read_data(self, filename: str):

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
            raise AnsibleError('Unable to read source file (%s): %s' % (to_native(filename), msg))

        return data

    def write_data(self, data: t.AnyStr, thefile: str, shred: bool = True, mode: int = 0o600):
        # TODO: add docstrings for arg types since this code is picky about that
        """Write the data bytes to given path

        This is used to write a byte string to a file or stdout. It is used for
        writing the results of vault encryption or decryption. It is used for
        saving the ciphertext after encryption and it is also used for saving the
        plaintext after decrypting a vault. The type of the 'data' arg should be bytes,
        since in the plaintext case, the original contents can be of any text encoding
        or arbitrary binary data.

        When used to write the result of vault encryption, the value of the 'data' arg
        should be a utf-8 encoded byte string and not a text type.

        When used to write the result of vault decryption, the value of the 'data' arg
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
            if not os.access(os.path.dirname(thefile), os.W_OK):
                raise AnsibleError("Destination '%s' not writable" % (os.path.dirname(thefile)))
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

    def shuffle_files(self, src: str, dest: str):
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

    def _editor_shell_command(self, filename: str):
        env_editor = C.config.get_config_value('EDITOR')
        editor = shlex.split(env_editor)
        editor.append(filename)

        return editor
