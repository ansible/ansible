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
import subprocess
import sys
import tempfile
import warnings
from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError
from hashlib import md5
from hashlib import sha256
from io import BytesIO

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

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible import constants as C
from ansible.module_utils.six import PY3, binary_type
# Note: on py2, this zip is izip not the list based zip() builtin
from ansible.module_utils.six.moves import zip
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.utils.path import makedirs_safe

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


class AnsibleVaultPasswordError(AnsibleVaultError):
    pass


class AnsibleVaultFormatError(AnsibleError):
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


def _parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None):

    b_tmpdata = b_vaulttext_envelope.splitlines()
    b_tmpheader = b_tmpdata[0].strip().split(b';')

    b_version = b_tmpheader[1].strip()
    cipher_name = to_text(b_tmpheader[2].strip())
    vault_id = default_vault_id

    # Only attempt to find vault_id if the vault file is version 1.2 or newer
    # if self.b_version == b'1.2':
    if len(b_tmpheader) >= 4:
        vault_id = to_text(b_tmpheader[3].strip())

    b_ciphertext = b''.join(b_tmpdata[1:])

    return b_ciphertext, b_version, cipher_name, vault_id


def parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None, filename=None):
    """Parse the vaulttext envelope

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
        msg = "Vault envelope format error"
        if filename:
            msg += ' in %s' % (filename)
        msg += ': %s' % exc
        raise AnsibleVaultFormatError(msg)


def format_vaulttext_envelope(b_ciphertext, cipher_name, version=None, vault_id=None):
    """ Add header and format to 80 columns

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
    try:
        return unhexlify(b_data)
    except (BinasciiError, TypeError) as exc:
        raise AnsibleVaultFormatError('Vault format unhexlify error: %s' % exc)


def _parse_vaulttext(b_vaulttext):
    b_vaulttext = _unhexlify(b_vaulttext)
    b_salt, b_crypted_hmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
    b_salt = _unhexlify(b_salt)
    b_ciphertext = _unhexlify(b_ciphertext)

    return b_ciphertext, b_salt, b_crypted_hmac


def parse_vaulttext(b_vaulttext):
    """Parse the vaulttext

    :arg b_vaulttext: byte str containing the vaulttext (ciphertext, salt, crypted_hmac)
    :returns: A tuple of byte str of the ciphertext suitable for passing to a
        Cipher class's decrypt() function, a byte str of the salt,
        and a byte str of the crypted_hmac
    :raises: AnsibleVaultFormatError: if the vaulttext format is invalid
    """
    # SPLIT SALT, DIGEST, AND DATA
    try:
        return _parse_vaulttext(b_vaulttext)
    except AnsibleVaultFormatError:
        raise
    except Exception as exc:
        msg = "Vault vaulttext format error: %s" % exc
        raise AnsibleVaultFormatError(msg)


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
    this_path = os.path.realpath(os.path.expanduser(filename))

    if not os.path.exists(this_path):
        raise AnsibleError("The vault password file %s was not found" % this_path)

    if loader.is_executable(this_path):
        if script_is_client(filename):
            display.vvvv('The vault password file %s is a client script.' % filename)
            # TODO: pass vault_id_name to script via cli
            return ClientScriptVaultSecret(filename=this_path, vault_id=vault_id,
                                           encoding=encoding, loader=loader)
        # just a plain vault password script. No args, returns a byte array
        return ScriptVaultSecret(filename=this_path, encoding=encoding, loader=loader)

    return FileVaultSecret(filename=this_path, encoding=encoding, loader=loader)


# TODO: mv these classes to a seperate file so we don't pollute vault with 'subprocess' etc
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
            f = open(filename, "rb")
            vault_pass = f.read().strip()
            f.close()
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
        verify_secret_is_not_empty(vault_pass,
                                   msg=empty_password_msg)

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
        display.vvvv('Executing vault password client script: %s --vault-id %s' % (filename, vault_id))

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
    if not secrets:
        return []

    matches = [(vault_id, secret) for vault_id, secret in secrets if vault_id in target_vault_ids]
    return matches


def match_best_secret(secrets, target_vault_ids):
    '''Find the best secret from secrets that matches target_vault_ids

    Since secrets should be ordered so the early secrets are 'better' than later ones, this
    just finds all the matches, then returns the first secret'''
    matches = match_secrets(secrets, target_vault_ids)
    if matches:
        return matches[0]
    # raise exception?
    return None


def match_encrypt_vault_id_secret(secrets, encrypt_vault_id=None):
    # See if the --encrypt-vault-id matches a vault-id
    display.vvvv('encrypt_vault_id=%s' % encrypt_vault_id)

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

    display.vvvv('encrypt_vault_id=%s' % encrypt_vault_id)
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
    def __init__(self, secrets=None):
        self.secrets = secrets or []
        self.cipher_name = None
        self.b_version = b'1.2'

    def encrypt(self, plaintext, secret=None, vault_id=None):
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
        if vault_id:
            display.vvvvv('Encrypting with vault_id "%s" and vault secret %s' % (vault_id, secret))
        else:
            display.vvvvv('Encrypting without a vault_id using vault secret %s' % secret)

        b_ciphertext = this_cipher.encrypt(b_plaintext, secret)

        # format the data for output to the file
        b_vaulttext = format_vaulttext_envelope(b_ciphertext,
                                                self.cipher_name,
                                                vault_id=vault_id)
        return b_vaulttext

    def decrypt(self, vaulttext, filename=None):
        '''Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :kwarg filename: a filename that the data came from.  This is only
            used to make better error messages in case the data cannot be
            decrypted.
        :returns: a byte string containing the decrypted data and the vault-id that was used

        '''
        plaintext, vault_id, vault_secret = self.decrypt_and_get_vault_id(vaulttext, filename=filename)
        return plaintext

    def decrypt_and_get_vault_id(self, vaulttext, filename=None):
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
            raise AnsibleVaultError("A vault password must be specified to decrypt data")

        if not is_encrypted(b_vaulttext):
            msg = "input is not vault encrypted data"
            if filename:
                msg += "%s is not a vault encrypted file" % to_native(filename)
            raise AnsibleError(msg)

        b_vaulttext, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext,
                                                                             filename=filename)

        # create the cipher object, note that the cipher used for decrypt can
        # be different than the cipher used for encrypt
        if cipher_name in CIPHER_WHITELIST:
            this_cipher = CIPHER_MAPPING[cipher_name]()
        else:
            raise AnsibleError("{0} cipher could not be found".format(cipher_name))

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

        if vault_id:
            display.vvvvv('Found a vault_id (%s) in the vaulttext' % (vault_id))
            vault_id_matchers.append(vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv('We have a secret associated with vault id (%s), will try to use to decrypt %s' % (vault_id, to_text(filename)))
            else:
                display.vvvvv('Found a vault_id (%s) in the vault text, but we do not have a associated secret (--vault-id)' % (vault_id))

        # Not adding the other secrets to vault_secret_ids enforces a match between the vault_id from the vault_text and
        # the known vault secrets.
        if not C.DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault_id])

        matched_secrets = match_secrets(self.secrets, vault_id_matchers)

        # for vault_secret_id in vault_secret_ids:
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv('Trying to use vault secret=(%s) id=%s to decrypt %s' % (vault_secret, vault_secret_id, to_text(filename)))

            try:
                # secret = self.secrets[vault_secret_id]
                display.vvvv('Trying secret %s for vault_id=%s' % (vault_secret, vault_secret_id))
                b_plaintext = this_cipher.decrypt(b_vaulttext, vault_secret)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    file_slug = ''
                    if filename:
                        file_slug = ' of "%s"' % filename
                    display.vvvvv('Decrypt%s successful with secret=%s and vault_id=%s' % (file_slug, vault_secret, vault_secret_id))
                    break
            except AnsibleVaultFormatError as exc:
                msg = "There was a vault format error"
                if filename:
                    msg += ' in %s' % (to_text(filename))
                msg += ': %s' % exc
                display.warning(msg)
                raise
            except AnsibleError as e:
                display.vvvv('Tried to use the vault secret (%s) to decrypt (%s) but it failed. Error: %s' %
                             (vault_secret_id, to_text(filename), e))
                continue
        else:
            msg = "Decryption failed (no vault secrets were found that could decrypt)"
            if filename:
                msg += " on %s" % to_native(filename)
            raise AnsibleVaultError(msg)

        if b_plaintext is None:
            msg = "Decryption failed"
            if filename:
                msg += " on %s" % to_native(filename)
            raise AnsibleError(msg)

        return b_plaintext, vault_id_used, vault_secret_used


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
                for _ in range(passes):
                    fh.seek(0, 0)
                    # get a random chunk of data, each pass with other length
                    chunk_len = random.randint(max_chunk_len // 2, max_chunk_len)
                    data = os.urandom(chunk_len)

                    for _ in range(0, file_len // chunk_len):
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
            # ValueError caught because OS X El Capitan is raising an
            # exception big enough to hit a limit in python2-2.7.11 and below.
            # Symptom is ValueError: insecure pickle when shred is not
            # installed there.
            r = 1

        if r != 0:
            # we could not successfully execute unix shred; therefore, do custom shred.
            self._shred_file_custom(tmp_path)

        os.remove(tmp_path)

    def _edit_file_helper(self, filename, secret,
                          existing_data=None, force_save=False, vault_id=None):

        # Create a tempfile
        root, ext = os.path.splitext(os.path.realpath(filename))
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)

        try:
            if existing_data:
                self.write_data(existing_data, tmp_path, shred=False)

            # drop the user into an editor on the tmp file
            subprocess.call(self._editor_shell_command(tmp_path))
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
        b_ciphertext = self.vault.encrypt(b_tmpdata, secret, vault_id=vault_id)
        self.write_data(b_ciphertext, tmp_path)

        # shuffle tmp file into place
        self.shuffle_files(tmp_path, filename)
        display.vvvvv('Saved edited file "%s" encrypted using %s and  vault id "%s"' % (filename, secret, vault_id))

    def _real_path(self, filename):
        # '-' is special to VaultEditor, dont expand it.
        if filename == '-':
            return filename

        real_path = os.path.realpath(filename)
        return real_path

    def encrypt_bytes(self, b_plaintext, secret, vault_id=None):

        b_ciphertext = self.vault.encrypt(b_plaintext, secret, vault_id=vault_id)

        return b_ciphertext

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
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))
        self.write_data(plaintext, output_file or filename, shred=False)

    def create_file(self, filename, secret, vault_id=None):
        """ create a new encrypted file """

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            display.warning("%s does not exist, creating..." % dirname)
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

        try:
            # vaulttext gets converted back to bytes, but alas
            # TODO: return the vault_id that worked?
            plaintext, vault_id_used, vault_secret_used = self.vault.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))

        # Figure out the vault id from the file, to select the right secret to re-encrypt it
        # (duplicates parts of decrypt, but alas...)
        dummy, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext,
                                                                       filename=filename)

        # vault id here may not be the vault id actually used for decrypting
        # as when the edited file has no vault-id but is decrypted by non-default id in secrets
        # (vault_id=default, while a different vault-id decrypted)

        # Keep the same vault-id (and version) as in the header
        if cipher_name not in CIPHER_WRITE_WHITELIST:
            # we want to get rid of files encrypted with the AES cipher
            self._edit_file_helper(filename, vault_secret_used, existing_data=plaintext,
                                   force_save=True, vault_id=vault_id)
        else:
            self._edit_file_helper(filename, vault_secret_used, existing_data=plaintext,
                                   force_save=False, vault_id=vault_id)

    def plaintext(self, filename):

        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        try:
            plaintext = self.vault.decrypt(vaulttext, filename=filename)
            return plaintext
        except AnsibleError as e:
            raise AnsibleVaultError("%s for %s" % (to_bytes(e), to_bytes(filename)))

    # FIXME/TODO: make this use VaultSecret
    def rekey_file(self, filename, new_vault_secret, new_vault_id=None):

        # follow the symlink
        filename = self._real_path(filename)

        prev = os.stat(filename)
        b_vaulttext = self.read_data(filename)
        vaulttext = to_text(b_vaulttext)

        display.vvvvv('Rekeying file "%s" to with new vault-id "%s" and vault secret %s' %
                      (filename, new_vault_id, new_vault_secret))
        try:
            plaintext, vault_id_used, _dummy = self.vault.decrypt_and_get_vault_id(vaulttext)
        except AnsibleError as e:
            raise AnsibleError("%s for %s" % (to_bytes(e), to_bytes(filename)))

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

        display.vvvvv('Rekeyed file "%s" (decrypted with vault id "%s") was encrypted with new vault-id "%s" and vault secret %s' %
                      (filename, vault_id_used, new_vault_id, new_vault_secret))

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
        env_editor = os.environ.get('EDITOR', 'vi')
        editor = shlex.split(env_editor)
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

    @staticmethod
    def _parse_plaintext_envelope(b_envelope):
        # split out sha and verify decryption
        b_split_data = b_envelope.split(b"\n", 1)
        b_this_sha = b_split_data[0]
        b_plaintext = b_split_data[1]
        b_test_sha = to_bytes(sha256(b_plaintext).hexdigest())

        return b_plaintext, b_this_sha, b_test_sha

    @classmethod
    def _decrypt_cryptography(cls, b_salt, b_ciphertext, b_password, key_length):

        bs = algorithms.AES.block_size // 8
        b_key, b_iv = cls._aes_derive_key_and_iv(b_password, b_salt, key_length, bs)
        cipher = C_Cipher(algorithms.AES(b_key), modes.CBC(b_iv), CRYPTOGRAPHY_BACKEND).decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

        try:
            b_plaintext_envelope = unpadder.update(
                cipher.update(b_ciphertext) + cipher.finalize()
            ) + unpadder.finalize()
        except ValueError:
            # In VaultAES, ValueError: invalid padding bytes can mean bad
            # password was given
            raise AnsibleError("Decryption failed")

        b_plaintext, b_this_sha, b_test_sha = cls._parse_plaintext_envelope(b_plaintext_envelope)

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
        b_plaintext_envelope = out_file.read()
        out_file.close()

        b_plaintext, b_this_sha, b_test_sha = cls._parse_plaintext_envelope(b_plaintext_envelope)

        if b_this_sha != b_test_sha:
            raise AnsibleError("Decryption failed")

        return b_plaintext

    @classmethod
    def decrypt(cls, b_vaulttext, secret, key_length=32):

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

        b_vaultdata = _unhexlify(b_vaulttext)
        b_salt = b_vaultdata[len(b'Salted__'):16]
        b_ciphertext = b_vaultdata[16:]

        b_password = secret.bytes

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

        return to_bytes(hexlify(b_hmac), errors='surrogate_or_strict'), hexlify(b_ciphertext)

    @staticmethod
    def _encrypt_pycrypto(b_plaintext, b_key1, b_key2, b_iv):
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
    def encrypt(cls, b_plaintext, secret):
        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')
        b_salt = os.urandom(32)
        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv)
        elif HAS_PYCRYPTO:
            b_hmac, b_ciphertext = cls._encrypt_pycrypto(b_plaintext, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in encrypt)')

        b_vaulttext = b'\n'.join([hexlify(b_salt), b_hmac, b_ciphertext])
        # Unnecessary but getting rid of it is a backwards incompatible vault
        # format change
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    @classmethod
    def _decrypt_cryptography(cls, b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        # b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)
        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(_unhexlify(b_crypted_hmac))
        except InvalidSignature as e:
            raise AnsibleVaultError('HMAC verification failed: %s' % e)

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
    def decrypt(cls, b_vaulttext, secret):

        b_ciphertext, b_salt, b_crypted_hmac = parse_vaulttext(b_vaulttext)

        # TODO: would be nice if a VaultSecret could be passed directly to _decrypt_*
        #       (move _gen_key_initctr() to a AES256 VaultSecret or VaultContext impl?)
        # though, likely needs to be python cryptography specific impl that basically
        # creates a Cipher() with b_key1, a Mode.CTR() with b_iv, and a HMAC() with sign key b_key2
        b_password = secret.bytes

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
