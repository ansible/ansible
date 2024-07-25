# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

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
import warnings
import pickle

from abc import abstractmethod
from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError

HAS_CRYPTOGRAPHY = False
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

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible import constants as C
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe, unfrackpath

display = Display()


b_HEADER = b'$ANSIBLE_VAULT'
NEED_CRYPTO_LIBRARY = "Ansible's Vault requires the cryptography library in order to function"
VALID_VERSIONS = frozenset(['1.1', '1.2', '1.3'])


# Future: move to ansible.errors
class AnsibleVaultError(AnsibleError):

    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=False, orig_exc=None, filename=None):

        self.filename = filename
        super(AnsibleVaultError, self).__init__(message, obj, show_content, suppress_extended_error, orig_exc)


class AnsibleVaultPasswordError(AnsibleVaultError):
    pass


class AnsibleVaultFormatError(AnsibleVaultError):
    pass


# After backport: add type validation
# Also move more functions to vault object
#'is_vault/is_vaulted_filed' might be less ambigious naming
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


def _parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None):
    """ DEPRECATED, kept until we can do formal deprecation in 2.18 """

    b_tmpdata = b_vaulttext_envelope.splitlines()
    b_tmpheader = b_tmpdata[0].strip().split(b';')

    b_version = b_tmpheader[1].strip()
    cipher_name = to_text(b_tmpheader[2].strip())
    vault_id = default_vault_id

    # Only attempt to find vault_id if the vault file is version 1.2 or newer
    if len(b_tmpheader) >= 4:
        vault_id = to_text(b_tmpheader[3].strip())

    b_ciphertext = b''.join(b_tmpdata[1:])

    return b_ciphertext, b_version, cipher_name, vault_id


def parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None, filename=None):
    """ DEPRECATED, use Vault.from_envelope(), kept until we can do formal deprecation in 2.18

    Parse the vaulttext envelope

    When data is saved, it has a header prepended and is formatted into 80
    character lines.  This method extracts the information from the header
    and then removes the header and the inserted newlines.  The string returned
    is suitable for processing by the Cipher classes.

    :arg b_vaulttext: byte str containing the data from a save file
    :kwarg default_vault_id: The vault_id name to use if the vaulttext does not provide one.
    :kwarg filename: The filename that the data came from.  This is only
        used to make better error messages in case the data cannot be
        decrypted. This is optional.
    :returns: A tuple of byte str of the vaulttext suitable to pass to parse_vaultext,
        a byte str of the vault format version,
        the name of the cipher used, and the vault_id.
    :raises: AnsibleVaultFormatError: if the vaulttext_envelope format is invalid
    """
    # used by decrypt
    default_vault_id = default_vault_id or C.DEFAULT_VAULT_IDENTITY

    try:
        return _parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id)
    except Exception as exc:
        raise AnsibleVaultFormatError('Vault envelope format error', filename=filename, orig_exc=exc)


def format_vaulttext_envelope(b_ciphertext, cipher_name, version=None, vault_id=None):
    """ DEPRECATED, use Vault.to_envelope(), kept until we can do formal deprecation in 2.18

        Add header and format to 80 columns

        :arg b_ciphertext: the encrypted and hexlified data as a byte string
        :arg cipher_name: unicode cipher name (for ex, u'AES256')
        :arg version: unicode vault version (for ex, '1.2'). Optional ('1.1' is default)
        :arg vault_id: unicode vault identifier. If provided, the version will be bumped to 1.2.
        :returns: a byte str that should be dumped into a file.  It's
            formatted to 80 char columns and has the header prepended
    """

    if not cipher_name:
        raise AnsibleError("the cipher must be set before adding a header")

    version = version or '1.1'

    # If we specify a vault_id, use format version 1.2. For no vault_id, stick to 1.1
    if vault_id and vault_id != u'default':
        version = '1.2'

    b_version = to_bytes(version, 'utf-8', errors='strict')
    b_vault_id = to_bytes(vault_id, 'utf-8', errors='strict')
    b_cipher_name = to_bytes(cipher_name, 'utf-8', errors='strict')

    header_parts = [b_HEADER,
                    b_version,
                    b_cipher_name]

    if b_version == b'1.2' and b_vault_id:
        header_parts.append(b_vault_id)

    header = b';'.join(header_parts)

    b_vaulttext = [header]
    b_vaulttext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
    b_vaulttext += [b'']
    b_vaulttext = b'\n'.join(b_vaulttext)

    return b_vaulttext


def _unhexlify(b_data):
    ''' unhexlify but with our own error handling '''
    try:
        return unhexlify(b_data)
    except (BinasciiError, TypeError) as exc:
        raise ValueError('Invalid vault data forced unhexlify errors', orig_exc=exc)


def parse_vaulttext(b_vaulttext):
    ''' old format does double hexing, so need double unhexing,
        only use with versions 1.1 and 1.2
    :arg b_vaulttext: byte str containing the vaulttext (ciphertext, salt, crypted_hmac)
    :returns: A tuple of byte str of the ciphertext suitable for passing to a
        Cipher class's decrypt() function, a byte str of the salt,
        and a byte str of the crypted_hmac
    :raises: AnsibleVaultFormatError: if the vaulttext format is invalid
    '''
    try:
        return [_unhexlify(x) for x in _unhexlify(b_vaulttext).split(b"\n", 2)]
    except ValueError as exc:
        raise AnsibleVaultFormatError("Invalid Vault vaulttext format", orig_exc=exc)


def verify_secret_is_not_empty(secret, msg=None):
    '''Check the secret against minimal requirements.

    Raises: AnsibleVaultPasswordError if the password does not meet requirements.

    Currently, only requirement is that the password is not None or an empty string.
    '''
    msg = msg or 'Invalid vault password was provided'
    if not secret:
        raise AnsibleVaultPasswordError(msg)


class VaultSecret:
    '''Opaque/abstract objects for a single vault secret. ie, a password or a key.'''

    def __init__(self, _bytes=None):
        # FIXME: ? that seems wrong... Unset etc?
        self._bytes = _bytes

    @property
    def bytes(self):
        '''The secret as a bytestring.

        Sub classes that store text types will need to override to encode the text to bytes.
        '''
        return self._bytes

    def load(self):
        return self._bytes


class PromptVaultSecret(VaultSecret):
    default_prompt_formats = ["Vault password (%s): "]

    def __init__(self, _bytes=None, vault_id=None, prompt_formats=None):
        super(PromptVaultSecret, self).__init__(_bytes=_bytes)
        self.vault_id = vault_id

        if prompt_formats is None:
            self.prompt_formats = self.default_prompt_formats
        else:
            self.prompt_formats = prompt_formats

    @property
    def bytes(self):
        return self._bytes

    def load(self):
        self._bytes = self.ask_vault_passwords()

    def ask_vault_passwords(self):
        b_vault_passwords = []

        for prompt_format in self.prompt_formats:
            prompt = prompt_format % {'vault_id': self.vault_id}
            try:
                vault_pass = display.prompt(prompt, private=True)
            except EOFError:
                raise AnsibleVaultError('EOFError (ctrl-d) on prompt for (%s)' % self.vault_id)

            verify_secret_is_not_empty(vault_pass)

            b_vault_pass = to_bytes(vault_pass, errors='strict', nonstring='simplerepr').strip()
            b_vault_passwords.append(b_vault_pass)

        # Make sure the passwords match by comparing them all to the first password
        for b_vault_password in b_vault_passwords:
            self.confirm(b_vault_passwords[0], b_vault_password)

        if b_vault_passwords:
            return b_vault_passwords[0]

        return None

    def confirm(self, b_vault_pass_1, b_vault_pass_2):
        # enforce no newline chars at the end of passwords

        if b_vault_pass_1 != b_vault_pass_2:
            # FIXME: more specific exception
            raise AnsibleError("Passwords do not match")


def script_is_client(filename):
    '''Determine if a vault secret script is a client script that can be given --vault-id args'''

    # if password script is 'something-client' or 'something-client.[sh|py|rb|etc]'
    # script_name can still have '.' or could be entire filename if there is no ext
    script_name, dummy = os.path.splitext(filename)

    # TODO: for now, this is entirely based on filename
    if script_name.endswith('-client'):
        return True

    return False


def get_file_vault_secret(filename=None, vault_id=None, encoding=None, loader=None):
    ''' Get secret from file content or execute file and get secret from stdout '''

    # we unfrack but not follow the full path/context to possible vault script
    # so when the script uses 'adjacent' file for configuration or similar
    # it still works (as inventory scripts often also do).
    # while files from --vault-password-file are already unfracked, other sources are not
    this_path = unfrackpath(filename, follow=False)
    if not os.path.exists(this_path):
        raise AnsibleError("The vault password file %s was not found" % this_path)

    if os.path.isdir(this_path):
        raise AnsibleError(f"The vault password file provided '{this_path}' can not be a directory")

    # it is a script?
    if loader.is_executable(this_path):

        if script_is_client(filename):
            # this is special script type that handles vault ids
            display.vvvv(u'The vault password file %s is a client script.' % to_text(this_path))
            # TODO: pass vault_id_name to script via cli
            return ClientScriptVaultSecret(filename=this_path, vault_id=vault_id, encoding=encoding, loader=loader)

        # just a plain vault password script. No args, returns a byte array
        return ScriptVaultSecret(filename=this_path, encoding=encoding, loader=loader)

    return FileVaultSecret(filename=this_path, encoding=encoding, loader=loader)


# TODO: mv these classes to a separate file so we don't pollute vault with 'subprocess' etc
class FileVaultSecret(VaultSecret):
    def __init__(self, filename=None, encoding=None, loader=None):
        super(FileVaultSecret, self).__init__()
        self.filename = filename
        self.loader = loader

        self.encoding = encoding or 'utf8'

        # We could load from file here, but that is eventually a pain to test
        self._bytes = None
        self._text = None

    @property
    def bytes(self):
        if self._bytes:
            return self._bytes
        if self._text:
            return self._text.encode(self.encoding)
        return None

    def load(self):
        self._bytes = self._read_file(self.filename)

    def _read_file(self, filename):
        """
        Read a vault password from a file or if executable, execute the script and
        retrieve password from STDOUT
        """

        # TODO: replace with use of self.loader
        try:
            with open(filename, "rb") as f:
                vault_pass = f.read().strip()
        except (OSError, IOError) as e:
            raise AnsibleError("Could not read vault password file %s: %s" % (filename, e))

        b_vault_data, dummy = self.loader._decrypt_if_vault_data(vault_pass, filename)

        vault_pass = b_vault_data.strip(b'\r\n')

        verify_secret_is_not_empty(vault_pass,
                                   msg='Invalid vault password was provided from file (%s)' % filename)

        return vault_pass

    def __repr__(self):
        if self.filename:
            return "%s(filename='%s')" % (self.__class__.__name__, self.filename)
        return "%s()" % (self.__class__.__name__)


class ScriptVaultSecret(FileVaultSecret):
    def _read_file(self, filename):
        if not self.loader.is_executable(filename):
            raise AnsibleVaultError("The vault password script %s was not executable" % filename)

        command = self._build_command()

        stdout, stderr, p = self._run(command)

        self._check_results(stdout, stderr, p)

        vault_pass = stdout.strip(b'\r\n')

        empty_password_msg = 'Invalid vault password was provided from script (%s)' % filename
        verify_secret_is_not_empty(vault_pass, msg=empty_password_msg)

        return vault_pass

    def _run(self, command):
        try:
            # STDERR not captured to make it easier for users to prompt for input in their scripts
            p = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError as e:
            msg_format = "Problem running vault password script %s (%s)." \
                " If this is not a script, remove the executable bit from the file."
            msg = msg_format % (self.filename, e)

            raise AnsibleError(msg)

        stdout, stderr = p.communicate()
        return stdout, stderr, p

    def _check_results(self, stdout, stderr, popen):
        if popen.returncode != 0:
            raise AnsibleError("Vault password script %s returned non-zero (%s): %s" %
                               (self.filename, popen.returncode, stderr))

    def _build_command(self):
        return [self.filename]


class ClientScriptVaultSecret(ScriptVaultSecret):
    VAULT_ID_UNKNOWN_RC = 2

    def __init__(self, filename=None, encoding=None, loader=None, vault_id=None):
        super(ClientScriptVaultSecret, self).__init__(filename=filename,
                                                      encoding=encoding,
                                                      loader=loader)
        self._vault_id = vault_id
        display.vvvv(u'Executing vault password client script: %s --vault-id %s' % (to_text(filename), to_text(vault_id)))

    def _run(self, command):
        try:
            p = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except OSError as e:
            msg_format = "Problem running vault password client script %s (%s)." \
                " If this is not a script, remove the executable bit from the file."
            msg = msg_format % (self.filename, e)

            raise AnsibleError(msg)

        stdout, stderr = p.communicate()
        return stdout, stderr, p

    def _check_results(self, stdout, stderr, popen):
        if popen.returncode == self.VAULT_ID_UNKNOWN_RC:
            raise AnsibleError('Vault password client script %s did not find a secret for vault-id=%s: %s' %
                               (self.filename, self._vault_id, stderr))

        if popen.returncode != 0:
            raise AnsibleError("Vault password client script %s returned non-zero (%s) when getting secret for vault-id=%s: %s" %
                               (self.filename, popen.returncode, self._vault_id, stderr))

    def _build_command(self):
        command = [self.filename]
        if self._vault_id:
            command.extend(['--vault-id', self._vault_id])

        return command

    def __repr__(self):
        if self.filename:
            return "%s(filename='%s', vault_id='%s')" % \
                (self.__class__.__name__, self.filename, self._vault_id)
        return "%s()" % (self.__class__.__name__)


def match_secrets(secrets, target_vault_ids):
    '''Find all VaultSecret objects that are mapped to any of the target_vault_ids in secrets'''
    matches = []
    if secrets:
        matches = [(vault_id, secret) for vault_id, secret in secrets if vault_id in target_vault_ids]
    return matches


def match_best_secret(secrets, target_vault_ids):
    '''Find the best secret from secrets that matches target_vault_ids
    Since secrets should be ordered so the early secrets are 'better' than later ones, this
    just finds all the matches, then returns the first secret'''
    matches = match_secrets(secrets, target_vault_ids)
    if matches:
        return matches[0]
    return None


def match_encrypt_vault_id_secret(secrets, encrypt_vault_id=None):
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


def match_encrypt_secret(secrets, encrypt_vault_id=None):
    '''Find the best/first/only secret in secrets to use for encrypting'''

    display.vvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))
    # See if the --encrypt-vault-id matches a vault-id
    if encrypt_vault_id:
        return match_encrypt_vault_id_secret(secrets,
                                             encrypt_vault_id=encrypt_vault_id)

    # Find the best/first secret from secrets since we didnt specify otherwise
    # ie, consider all of the available secrets as matches
    _vault_id_matchers = [_vault_id for _vault_id, dummy in secrets]
    best_secret = match_best_secret(secrets, _vault_id_matchers)

    # can be empty list sans any tuple
    return best_secret


class VaultLib:
    def __init__(self, secrets=None, version=None, cipher=None):
        if version is not None and version not in VALID_VERSIONS:
            raise AnsibleVaultError("Invalid vault version supplied: %s, valid ones are %s" % (version, ', '.join(VALID_VERSIONS)))
        self.version = version
        self.cipher_name = cipher
        self.set_secrets(secrets)

    @staticmethod
    def is_encrypted(vaulttext):
        return is_encrypted(vaulttext)

    def set_secrets(self, secrets):
        if not secrets:
            self.secrets = []
        else:
            self.secrets = secrets

    def encrypt(self, plaintext, secret=None, vault_id=None, salt=None, version=None, cipher=None):
        """Vault encrypt a piece of data.

        :arg plaintext: a text or byte string to encrypt.
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

        # passed in version > vaultlib init version > config version
        if version is None:
            if self.version is None:
                version = C.config.get_config_value('VAULT_VERSION')
            else:
                version = self.version

        if cipher is None:
            # can still be none, Vault will choose defaults
            cipher = self.cipher_name

        v = Vault(version, vault_id, salt, cipher, plain=to_bytes(plaintext, errors='surrogate_or_strict'))

        if is_encrypted(v.plain):
            raise AnsibleError("input is already encrypted")

        this_cipher = v.get_crypt_class()

        # encrypt data
        if v.vault_id:
            display.vvvvv(u'Encrypting with vault_id "%s"' % (to_text(v.vault_id)))
        else:
            display.vvvvv(u'Encrypting without a vault_id')

        this_cipher.encrypt(v, secret)

        # format the data for output to the file
        return v.to_envelope()

    def decrypt(self, vaulttext, filename=None, obj=None):
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

    def decrypt_and_get_vault_id(self, vaulttext, filename=None, obj=None):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id vault-secret that was used

        """
        b_vaulttext = to_bytes(vaulttext, errors='strict', encoding='utf-8')

        if not is_encrypted(b_vaulttext):
            raise AnsibleVaultError("The input is not a valid encrypted vault", filename=filename)

        if not self.secrets:  # can be None or []
            raise AnsibleVaultError("A vault secret is required to decrypt data", filename=filename)

        b_plaintext = None
        vault = Vault.from_envelope(b_vaulttext, None, filename=filename)

        # Get the cipher class matching the vault envelope header
        this_cipher = vault.get_crypt_class()

        vault_id_matchers = []
        vault_id_used = None
        vault_secret_used = None

        # We check vault_id from envelope first, this is not cryptographically secure and can be tampered with
        if vault.vault_id:
            display.vvvvv(u'Found a vault_id (%s) in the vaulttext' % to_text(vault.vault_id))
            vault_id_matchers.append(vault.vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv(u'We have a secret associated with vault id (%s), will try to use to decrypt %s' % (vault.vault_id, vault.filename))
            else:
                display.vvvvv(u'Found a vault_id (%s) in the vault text, but we do not have a associated secret (--vault-id)' % vault.vault_id)

        # Configuration determines if we are strict on vault_id match or try all possible ones
        if not C.DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault.vault_id])

        # for use in info/error messages
        file_slug = ''
        if vault.filename:
            file_slug = to_text(' "%s"' % vault.filename)

        # iterate over all the applicable secrets until one works or none do
        matched_secrets = match_secrets(self.secrets, vault_id_matchers)
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv(u'Trying to use vault secret id=%s to decrypt%s' % (to_text(vault_secret_id), file_slug))
            try:
                b_plaintext = this_cipher.decrypt(vault, vault_secret)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    display.vvvvv(u'Decrypt%s successful with vault_id=%s' % (file_slug, to_text(vault_secret_id)))
                    break
            except AnsibleVaultFormatError as exc:
                exc.obj = obj
                exc.filename = filename
                raise exc
            except AnsibleError as e:
                display.vvvv(u'Tried to use the vault secret id (%s) to decrypt%s but it failed. Error: %s' %
                             (to_text(vault_secret_id), file_slug, e))
                continue
        else:
            # none worked!
            raise AnsibleVaultError("Decryption failed, no usable vault secrets were found", filename=vault.filename)

        if b_plaintext is None:
            raise AnsibleVaultError("Decryption failed", filename=vault.filename)

        return b_plaintext, vault_id_used, vault_secret_used


class VaultEditor:

    def __init__(self, vault=None):
        # TODO: it may be more useful to just make VaultSecrets and index of VaultLib objects...
        self.vaultlib = vault or VaultLib()

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
            raise AnsibleError('Unable to execute the command "%s": %s' % (' '.join(cmd), to_native(e)))

        b_tmpdata = self.read_data(tmp_path)

        # Do nothing if the content has not changed
        if force_save or existing_data != b_tmpdata:

            # encrypt new data and write out to tmp
            # An existing vaultfile will always be UTF-8,
            # so decode to unicode here
            b_ciphertext = self.vaultlib.encrypt(b_tmpdata, secret, vault_id=vault_id)
            self.write_data(b_ciphertext, tmp_path)

            # shuffle tmp file into place
            self.shuffle_files(tmp_path, filename)
            display.vvvvv(u'Saved edited file "%s" encrypted using %s and  vault id "%s"' % (to_text(filename), to_text(secret), to_text(vault_id)))

        # always shred temp, jic
        self._shred_file(tmp_path)

    def _real_path(self, filename):
        # '-' is special to VaultEditor, dont expand it.
        if filename == '-':
            return filename

        real_path = os.path.realpath(filename)
        return real_path

    def encrypt_bytes(self, b_plaintext, secret, vault_id=None):

        b_ciphertext = self.vaultlib.encrypt(b_plaintext, secret, vault_id=vault_id)

        return b_ciphertext

    def encrypt_file(self, filename, secret, vault_id=None, output_file=None):

        # A file to be encrypted into a vaultfile could be any encoding
        # so treat the contents as a byte string.

        # follow the symlink
        filename = self._real_path(filename)

        b_plaintext = self.read_data(filename)
        b_ciphertext = self.vaultlib.encrypt(b_plaintext, secret, vault_id=vault_id)
        self.write_data(b_ciphertext, output_file or filename)

    def decrypt_file(self, filename, output_file=None):

        # follow the symlink, read, decrypt and write
        filename = self._real_path(filename)
        ciphertext = self.read_data(filename)
        plaintext = self.vaultlib.decrypt(ciphertext, filename=filename)
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename, secret, vault_id=None):
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

    def edit_file(self, filename):
        vault_id_used = None
        vault_secret_used = None
        # follow the symlink
        filename = self._real_path(filename)

        b_vaulttext = self.read_data(filename)

        # vault or yaml files are always utf8
        vaulttext = to_text(b_vaulttext)

        # vaulttext gets converted back to bytes, but alas
        # TODO: return the vault_id that worked?
        plaintext, vault_id_used, vault_secret_used = self.vaultlib.decrypt_and_get_vault_id(vaulttext, filename=filename)

        # Figure out the vault id from the file, to select the right secret to re-encrypt it
        # (duplicates parts of decrypt, but alas...)
        vault = Vault.from_envelope(b_vaulttext, None, filename)

        # vault id here may not be the vault id actually used for decrypting
        # as when the edited file has no vault-id but is decrypted by non-default id in secrets
        # (vault_id=default, while a different vault-id decrypted)

        # we want to get rid of files encrypted with the AES cipher
        force_save = (vault.cipher not in vault.CIPHER_WRITE_ALLOWLIST)

        # Keep the same vault-id (and version) as in the header
        self._edit_file_helper(vault.filename, vault_secret_used, existing_data=plaintext, force_save=force_save, vault_id=vault.vault_id)

    def plaintext(self, filename):

        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)
        return self.vaultlib.decrypt(vaulttext, filename=filename)

    # FIXME/TODO: make this use VaultSecret
    def rekey_file(self, filename, new_vault_secret, new_vault_id=None):

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        display.vvvvv(u'Rekeying file "%s" to with new vault-id "%s" and vault secret %s' %
                      (to_text(filename), to_text(new_vault_id), to_text(new_vault_secret)))

        plaintext, vault_id_used, _dummy = self.vaultlib.decrypt_and_get_vault_id(vaulttext, filename=filename)

        # This is more or less an assert, see #18247
        if new_vault_secret is None:
            raise AnsibleError('The value for the new_password to rekey %s with is not valid' % filename)

        # FIXME: VaultContext...?  could rekey to a different vault_id in the same VaultSecrets

        # Need a new VaultLib because the new vault data can be a different
        # vault lib format or cipher (for ex, when we migrate 1.0 style vault data to
        # 1.1 style data we change the version and the cipher). This is where a VaultContext might help

        # the new vault will only be used for encrypting, so it doesn't need the vault secrets
        # (we will pass one in directly to encrypt)
        new_vault = VaultLib()
        b_new_vaulttext = new_vault.encrypt(plaintext, new_vault_secret, vault_id=new_vault_id)

        self.write_data(b_new_vaulttext, filename)

        # preserve permissions
        os.chmod(filename, prev.st_mode)
        os.chown(filename, prev.st_uid, prev.st_gid)

        display.vvvvv(u'Rekeyed file "%s" (decrypted with vault id "%s") was encrypted with new vault-id "%s" and vault secret %s' %
                      (to_text(filename), to_text(vault_id_used), to_text(new_vault_id), to_text(new_vault_secret)))

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
            raise AnsibleError('Unable to read source file (%s): %s' % (to_native(filename), msg))

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


########################################
#               CIPHERS                #
########################################
class VaultCipher:

    @classmethod
    @abstractmethod
    def encrypt(cls, vault, secret):
        pass

    @classmethod
    @abstractmethod
    def decrypt(cls, vault, secret):
        pass

    @staticmethod
    def _get_salt():
        custom_salt, origin = C.config.get_config_value_and_origin('VAULT_ENCRYPT_SALT')
        if custom_salt:
            if not origin.startswith('cli:'):
                display.warning('Using configured salt, reusing a salt across vaults is insecure')
        else:
            # Future: replace with call to ansible.utils.encrypt.random_salt(32)
            custom_salt = os.urandom(32)
        return to_bytes(custom_salt)

    @staticmethod
    def _is_equal(b_a, b_b):
        """
        Comparing 2 byte arrays in constant time to avoid timing attacks.
        It would be nice if there were a library for this but hey.
        http://codahale.com/a-lesson-in-timing-attacks/
        """
        if len(b_a) != len(b_b):
            return False

        result = 0
        for b_x, b_y in zip(b_a, b_b):
            result |= b_x ^ b_y
        return result == 0


class VaultAES256(VaultCipher):
    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2

    http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
    """
    # iterations is low and not recommended,
    # but cannot change as it is backwards incompatible, use AES256v2 instead
    defaults = {'iterations': 10000, 'key_length': 32}

    # Note: strings in this class should be byte strings by default.

    def __init__(self):
        if not HAS_CRYPTOGRAPHY:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + ' with AES cipher')

    @staticmethod
    def _require_crypto(f):
        def inner(self, *args, **kwargs):
            if HAS_CRYPTOGRAPHY:
                return f(self, *args, **kwargs)
            else:
                raise AnsibleError(NEED_CRYPTO_LIBRARY + ' with AES cipher')
        return inner

    @staticmethod
    def _create_key_cryptography(b_password, b_salt, options):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * options['key_length'] + options['iv_length'],
            salt=b_salt,
            iterations=options['iterations'],
            backend=CRYPTOGRAPHY_BACKEND)
        b_derivedkey = kdf.derive(b_password)

        return b_derivedkey

    @classmethod
    def _gen_key_initctr(cls, vault, b_password, b_salt):

        # Set defaults if they don't exist
        for opt in cls.defaults.keys():
            if opt not in vault.options:
                vault.options[opt] = cls.defaults[opt]

        # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
        if 'iv_length' not in vault.options:
            vault.options['iv_length'] = algorithms.AES.block_size // 8

        b_derivedkey = cls._create_key_cryptography(b_password, b_salt, vault.options)
        kl2 = vault.options['key_length'] * 2
        b_iv = b_derivedkey[kl2:kl2 + vault.options['iv_length']]

        b_key1 = b_derivedkey[:vault.options['key_length']]
        b_key2 = b_derivedkey[vault.options['key_length']:kl2]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return b_hmac, b_ciphertext

    @classmethod
    @_require_crypto
    def encrypt(cls, vault, secret):
        ''' Vault and VaultSecret objects '''

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if vault.salt is None:
            b_salt = cls._get_salt()
        elif not vault.salt:
            raise AnsibleVaultError('Empty or invalid salt passed to encrypt()')
        else:
            b_salt = to_bytes(vault.salt)

        b_password = secret.bytes  # method of all VaultSecret objects that returns actual secret
        b_key1, b_key2, b_iv = cls._gen_key_initctr(vault, b_password, b_salt)
        b_hmac, b_ciphertext = cls._encrypt_cryptography(vault.plain, b_key1, b_key2, b_iv)

        # Unnecessary hexlifying (done again in envelope), but kept for backwards compat, fixed AESv2/1.3
        vault.vaulted = b'\n'.join([hexlify(b_salt), hexlify(b_hmac), hexlify(b_ciphertext)])
        return vault.vaulted

    @classmethod
    def _decrypt_cryptography(cls, b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):

        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)

        try:
            # We verify that ciphered data was not tampered, don't even attempt decryption
            hmac.verify(b_crypted_hmac)
        except InvalidSignature as e:
            raise AnsibleVaultError('HMAC verification failed: %s' % e, orig_exc=e)

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(
            decryptor.update(b_ciphertext) + decryptor.finalize()
        ) + unpadder.finalize()

        return b_plaintext

    @classmethod
    @_require_crypto
    def decrypt(cls, vault, secret):
        try:
            b_salt, b_crypted_hmac, b_ciphertext = [_unhexlify(x) for x in vault.vaulted.split(b"\n", 2)]
        except ValueError as e:
            raise AnsibleVaultError("Invalid hexlified ciphered data in vault", orig_exc=e)

        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(vault, b_password, b_salt)

        vault.plain = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
        return vault.plain


class VaultAES256v2(VaultAES256):
    """
    Vault implementation derived from VaultAES256 with configurable options and
    avoids double hexlifying
    """

    # Values good as of 2Q/2024, can be updated at any time as
    # existing 1.3 vaults preserve the data
    defaults = {'iterations': 600000, 'key_length': 32}

    @classmethod
    @VaultAES256._require_crypto
    def encrypt(cls, vault, secret):

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if vault.salt is None:
            b_salt = cls._get_salt()
        elif not vault.salt:
            raise AnsibleVaultError('Empty or invalid salt passed to encrypt()', filename=vault.filename)
        else:
            b_salt = to_bytes(vault.salt)

        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(vault, b_password, b_salt)

        b_hmac, b_ciphertext = cls._encrypt_cryptography(vault.plain, b_key1, b_key2, b_iv)

        vault.vaulted = b'\n'.join([b_salt, b_hmac, b_ciphertext])
        return vault.vaulted

    @classmethod
    @VaultAES256._require_crypto
    def decrypt(cls, vault, secret):

        b_salt, b_crypted_hmac, b_ciphertext = vault.vaulted.split(b"\n", 2)
        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(vault, b_password, b_salt)

        vault.plain = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)

        return vault.plain


########################################
#       Vault envelope utility class   #
########################################
class Vault():

    b_vault_header = b'$ANSIBLE_VAULT'

    # Future proof: both of these this should be a bit more 'dynamic', specially as we add formats/ciphers
    OLD_FORMATS = ('1.1', '1.2')
    CIPHER_MAPPING = {
        u'AES256': VaultAES256,
        u'AES256v2': VaultAES256v2,
    }

    def __init__(self, version=C.VAULT_VERSION, vault_id=None, salt=None, cipher=None, options=None, filename=None, line=None, vaulted=None, plain=None):

        self.plain = plain
        self.vaulted = vaulted

        self.cipher = cipher
        self.salt = salt
        self.filename = filename
        self.line = line

        if vault_id is None:
            self.vault_id = C.DEFAULT_VAULT_IDENTITY
        else:
            self.vault_id = to_text(vault_id)

        self.version = to_text(version)

        if options is None:
            self.options = {}
        else:
            self.options = options
            # set default options

        # now set data depending on version
        if self.version in self.OLD_FORMATS:
            self.CIPHER_ALLOWLIST = frozenset(('AES256',))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256',))
            if self.version == '1.1':
                self.HEADER_LENGTH = 3
            else:
                # main diff of 1.2, store vault-id
                self.HEADER_LENGTH = 4
        else:
            # assume 1.3 until at least 1.4 is added
            self.CIPHER_ALLOWLIST = frozenset(('AES256', 'AES256v2'))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256v2',))
            # aside from vault-id in header we also have options dict
            self.HEADER_LENGTH = 5

        if self.cipher is not None and self.cipher not in self.CIPHER_WRITE_ALLOWLIST:
            display.warning("Invalid cipher selected (%s), ignoring and falling back to defaults." % self.cipher)
            self.cipher = None

        # set to default if not set
        if self.cipher is None:
            if self.version in Vault.OLD_FORMATS:
                self.cipher = "AES256"
            else:
                self.cipher = "AES256v2"

    @staticmethod
    def _is_valid(field_value, field_name):
        if not field_value:
            raise ValueError(f"Empty vault {field_name} field")
        elif b'\n' in field_value:
            raise ValueError(f"Invalid 'new line' found in vault envelope's {field_name} header: {field_value}")

    def get_crypt_class(self):
        """
            Return an instanciated object of the proper class to cipher/decipher this Vault object

            :returns: A subclass of VaultCipher that matches this Vault's assigned cipher
            :raises: AnsibleError: When no matching VaultCipher subclass is available
        """
        try:
            return self.CIPHER_MAPPING[self.cipher]()
        except KeyError:
            raise AnsibleError(u"{0} cipher could not be found".format(self.cipher))

    def to_envelope(self):
        """
            Serialize the Vault's ciphered text into a vaulted string fit for consumption for the Ansible runtime CLIs

            :returns: a byte str that contains the vaulted data.
                It formats the ciphertext to 80 char columns has the header line prepended for versions < 1.3.
                In versions >= 1.3 the header is prepended but the full content is 80 column formatted.

            :raises: AnsibleError: if the Vault object lacks the required information
        """

        if not self.cipher:
            raise AnsibleError("The cipher must be set before creating an envelope")

        if not self.vaulted:
            raise AnsibleError("Cannot create an envelope without encrypted content")

        # convert to bytes
        b_version = to_bytes(self.version, 'utf-8', errors='strict')
        b_vault_id = to_bytes(self.vault_id, 'utf-8', errors='strict')
        b_cipher = to_bytes(self.cipher, 'utf-8', errors='strict')

        header_parts = [self.b_vault_header, b_version, b_cipher]

        # 1.1 does not support vault id, rest do
        if b_version != b'1.1' and b_vault_id:
            header_parts.append(b_vault_id)

        h_vaulted = hexlify(self.vaulted)
        # compose envelope
        if self.version in self.OLD_FORMATS:
            # old formats (<1.3) do not support extended options
            # and header is alwasys on first line
            header = b';'.join(header_parts)
            b_envelope = [header]
            b_envelope += [h_vaulted[i:i + 80] for i in range(0, len(h_vaulted), 80)]
        else:
            # header can be multiline, include cipher as last element
            header_parts.append(hexlify(pickle.dumps(self.options)))
            header_parts.append(h_vaulted)
            header = b';'.join(header_parts)
            b_envelope = [header[i:i + 80] for i in range(0, len(header), 80)]

        b_envelope += [b'']

        return b'\n'.join(b_envelope)

    @classmethod
    def from_envelope(cls, b_envelope, default_vault_id, filename):
        """
        This method builds a Vault objected with data extracted from a vaulted string

        :arg b_envelope: A byte str containing the vaulted data
        :kwarg default_vault_id: The vault_id name to use if the vaulttext does not provide one,
            this only applies to the 1.1 format version
        :kwarg filename: Optional filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: A Vault object populated with the fields from the envelope.
        :raises: AnsibleVaultFormatError: if the vaulttext_envelope format is invalid

         Vaulted structures per version, both 'ciphertext' and 'pickled options hash' are hexlified
         $ANSIBLE_VAULT;1.1;AES256
         <ciphertext> # 80 column formatted

         $ANSIBLE_VAULT;1.2;AES256;example_vault_id
         <ciphertext> # 80 column formatted

         $ANSIBLE_VAULT;1.3;AES256;example_vault_id;<pickled_options_hash>;<ciphertext> # 80 column formatted

         header fields can be tampered with, we somewhat verify them but also we have 'sane defaults' when possible
        """
        # used by decrypt as default ...
        default_vault_id = default_vault_id or C.DEFAULT_VAULT_IDENTITY

        try:
            b_tmpheader = b_envelope.strip().split(b';')

            # start of first line is header in all versions, >= 1.3 it might span mulitple lines
            b_tag = b_tmpheader[0]
            b_version = b_tmpheader[1].strip()
            b_cipher = b_tmpheader[2].strip().splitlines()[0] # < 1.3 ciphertext will be present, so split lines

            # In future add hashing to verify these options were not tampered with, for now simple validation
            cls._is_valid(b_tag, 'tag')
            if b_tag != cls.b_vault_header:
                raise ValueError(f"Invalid or missing vault tag: {b_tag}")

            cls._is_valid(b_version, 'version')
            version = to_text(b_version, errors='surrogate_or_strict')

            # handle the differences between format versions
            if len(b_tmpheader) < 6:  # 1.3 has 6 fields
                # 1.1/1.2 have header in separate line and no options
                ciphertext = b''.join(b_envelope.splitlines()[1:])
                options = {}

                if len(b_tmpheader) > 3:
                    # 1.2 has 4 fields, 4th being vault id
                    b_vault_id = b_tmpheader[3].strip() or default_vault_id
                    b_cipher = b_cipher.splitlines()[0]  # remove extra stuff
                else:
                    # 1.1 only has 3 fields, no vault id
                    b_vault_id = default_vault_id
            else:
                # 1.3 format should have 6 fields
                b_vault_id = b_tmpheader[3].replace(b'\n', b'').strip() or default_vault_id
                b_options = b_tmpheader[4].replace(b'\n', b'') or {}
                ciphertext = b''.join(b_tmpheader[5].splitlines())
                options = pickle.loads(_unhexlify(b_options.strip(b';')))

            cls._is_valid(b_cipher , 'cipher')
            cipher = to_text(b_cipher)
            if cipher not in cls.CIPHER_MAPPING:
                # in future make this a warning?
                display.vvvv("Unsupported cipher '{cipher}' found in vault")

            if b_vault_id != default_vault_id:
                cls._is_valid(b_vault_id, 'vault_id')
            vault_id = to_text(b_vault_id)

            # actually from a vault object and assign the info we have
            v = cls(version, vault_id, None, cipher, options, filename, vaulted=_unhexlify(ciphertext))

        except Exception as exc:
            raise AnsibleVaultFormatError("Could not process vault envelope", filename=filename, orig_exc=exc)

        return v
