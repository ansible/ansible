# Copyright: (c) 2017, Ansible Project
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
import pickle
import tempfile
import warnings

import typing as t

from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError


from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible import constants as C
from ansible.module_utils.six import binary_type
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe, unfrackpath

if t.TYPE_CHECKING:
    from ansible.parsing.dataloader import DataLoader

display = Display()


# See also CIPHER_MAPPING at the bottom of the file which maps cipher strings
# (used in VaultFile header) to a cipher class

NEED_CRYPTO_LIBRARY = "ansible-vault requires the cryptography library in order to function"


class Vault():

    b_HEADER = b'$ANSIBLE_VAULT'

    def __init__(self, b_ciphertext, cipher, version='1.3', vault_id=None, options=None, filename=None, line=None):

        self._raw = b_ciphertext
        self.cipher = cipher
        self.version = version

        self.filename = filename
        self.line = line

        if options is None:
            self.options = {}

        if vault_id is None:
            self.vault_id = C.DEFAULT_VAULT_IDENTITY
        else:
            self.vault_id = vault_id

        # handle here or class per version?
        if self.version == '1.1'
        elif self.version == '1.2'
            self.HEADER_LENGTH = 4
            self.CIPHER_ALLOWLIST = frozenset(('AES256',))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256',))
        else:
            self.HEADER_LENGTH = 5
            self.CIPHER_ALLOWLIST = frozenset(('AES256','AES256v2'))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256v2',))

class Vault_1_1(Vault):
    HEADER_LENGTH = 3
    CIPHER_ALLOWLIST = frozenset(('AES256',))
    CIPHER_WRITE_ALLOWLIST = frozenset(('AES256',))
    VERSION = '1.1'

class Vault_1_2(Vault_1_1):
    HEADER_LENGTH = 4
    VERSION = '1.2'


class Vault_1_3(Vault):
    HEADER_LENGTH = 5
    CIPHER_ALLOWLIST = frozenset(('AES256','AES256v2'))
    CIPHER_WRITE_ALLOWLIST = frozenset(('AES256v2',))
    VERSION = '1.3'


class Version():
    ''' TODO: placeholder till i find alt to packaging '''
    pass


class AnsibleVaultError(AnsibleError):

    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=False, orig_exc=None, filename=None):

        self.filename = filename
        super(AnsibleVaultFormatError, self).__init__(message, obj, show_content, suppress_extended_error, orig_exc)

    @property
    def message(self):

        if filename:
            self._message += ' in "{self.filename}'
        super(AnsibleVaultFormatError, self).message()


class AnsibleVaultPasswordError(AnsibleVaultError):
    pass


class AnsibleVaultFormatError(AnsibleVaultError):
    pass


def is_encrypted(data: t.AnyStr) -> bool:
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

    return b_data.startswith(Vault.b_HEADER)


def is_encrypted_file(file_obj: t.IO[t.AnyStr], start_pos: int = 0, count: int = len(Vault.b_HEADER)):
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



def parse_vaulttext_envelope(b_vaulttext_envelope: bytes, default_vault_id: str | None = None, filename: t.AnyStr | None = None) -> Vault:
    """
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
        # examples per version
        # $ANSIBLE_VAULT;1.3;AES256;example1;<pickled_options_hash>
        # $ANSIBLE_VAULT;1.2;AES256;example1
        # $ANSIBLE_VAULT;1.1;AES256

        b_tmpdata = b_vaulttext_envelope.splitlines()
        b_tmpheader = b_tmpdata[0].strip().split(b';')

        b_ciphertext = b''.join(b_tmpdata[1:])

        while len(b_tmpheader) < 5:
            b_tmpheader.append(b'')

        b_tag, b_version, b_cipher, b_vault_id, b_options = [(x.strip()) for x in b_tmpheader]

        if b_tag != Vault.b_HEADER:
            raise AnsibleVaultFormatError(f"Invalid vault tag found: {b_tag}", filename=filename)

        if not b_vault_id:
            # This should be version 1.1 or a higher version w/o specific id
            vault_id = default_vault_id
        else:
            vault_id = str(vault_id)

        if b_options:
            options = pickle.loads(b_options)
        else:
            options = {}

    except Exception as exc:
        raise AnsibleVaultFormatError("Vault envelope format error", filename=filename, orig_exc=exc)

    return Vault(b_ciphertext, str(b_version), str(b_cipher), vault_id, options, filename)


def format_vaulttext_envelope(vault) -> bytes:
    """ Add header and format to 80 columns

        :arg vault: a vault class object
        :returns: a byte str that should be dumped into a file.  It's
            formatted to 80 char columns and has the header prepended
    """

    if not vault.cipher:
        raise AnsibleError("the cipher must be set before adding a header")

    version = vault.version

    # If we specify a vault_id, use format version 1.2. For no vault_id, stick to 1.1
    #if version <= '1.1' and vault_id and vault_id != u'default':
    #    version = '1.2'

    b_version = to_bytes(version, 'utf-8', errors='strict')
    b_vault_id = to_bytes(vault.vault_id, 'utf-8', errors='strict')
    b_cipher_name = to_bytes(vault.cipher, 'utf-8', errors='strict')
    b_options = pickle.dumps(vault.options)

    header_parts = [Vault.b_HEADER, b_version, b_cipher_name]

    if b_version != b'1.1' and b_vault_id:
        header_parts.append(b_vault_id)

    header = b';'.join(header_parts)

    b_vaulttext = [header]
    b_vaulttext += [vault.raw[i:i + 80] for i in range(0, len(vault.raw), 80)]
    b_vaulttext += [b'']
    b_vaulttext = b'\n'.join(b_vaulttext)

    return b_vaulttext


def verify_secret_is_not_empty(secret: t.AnyStr, msg: str | None = None):
    '''Check the secret against minimal requirements.

    Raises: AnsibleVaultPasswordError if the password does not meet requirements.

    Currently, only requirement is that the password is not None or an empty string.
    '''
    msg = msg or 'Invalid vault password was provided'
    if not secret:
        raise AnsibleVaultPasswordError(msg)


def script_is_client(filename: t.AnyStr) -> bool:
    '''Determine if a vault secret script is a client script that can be given --vault-id args'''

    # if password script is 'something-client' or 'something-client.[sh|py|rb|etc]'
    # script_name can still have '.' or could be entire filename if there is no ext
    script_name, dummy = os.path.splitext(filename)

    # TODO: for now, this is entirely based on filename
    if script_name.endswith('-client'):
        return True

    return False


def get_file_vault_secret(filename: t.AnyStr | None = None, vault_id: str | None = None, encoding: str | None = None, loader: DataLoader | None = None):
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
        return match_encrypt_vault_id_secret(secrets,
                                             encrypt_vault_id=encrypt_vault_id)

    # Find the best/first secret from secrets since we didnt specify otherwise
    # ie, consider all of the available secrets as matches
    _vault_id_matchers = [_vault_id for _vault_id, dummy in secrets]
    best_secret = match_best_secret(secrets, _vault_id_matchers)

    # can be empty list sans any tuple
    return best_secret
