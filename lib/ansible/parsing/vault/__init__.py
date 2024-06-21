# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pickle
import typing as t

from ansible.errors import AnsibleError, AnsibleVaultFormatError
from ansible import constants as C
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe, unfrackpath

# backwards compat
#from ansible.parsing.vault.manager import VaultLib, VaultEditor
#from ansible.parsing.vault.secrets import VaultSecret, get_file_vault_secret

if t.TYPE_CHECKING:
    from ansible.parsing.dataloader import DataLoader

display = Display()


# option: 1, version aware class
class Vault:

    b_HEADER = b'$ANSIBLE_VAULT'

    def __init__(self, cipher, version='1.3', vault_id=None, options=None, filename=None, line=None) -> t.Self:

        self.plain: str | None = None
        self.vaulted: bytes | None = None

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
        if self.version == '1.1':
            self.HEADER_LENGTH = 3
        elif self.version == '1.2':
            self.HEADER_LENGTH = 4
            self.CIPHER_ALLOWLIST = frozenset(('AES256',))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256',))
        else:
            self.HEADER_LENGTH = 5
            self.CIPHER_ALLOWLIST = frozenset(('AES256', 'AES256v2'))
            self.CIPHER_WRITE_ALLOWLIST = frozenset(('AES256v2',))

    # TODO: move hexing/unhexing into here as it is verion dependant
    # NOTE: should we just use python serialization methods?
    def to_envelope(self) -> bytes:
        """ Add header and format to 80 columns

            :returns: a byte str that should be dumped into a file.  It's
                formatted to 80 char columns and has the header prepended
        """

        if not self.cipher:
            raise AnsibleError("The cipher must be set before creating an envelope")

        if not self.vaulted:
            raise AnsibleError("Cannot create an envelope without encrypted content")

        # convert to bytes
        b_version = to_bytes(self.version, 'utf-8', errors='strict')
        b_vault_id = to_bytes(self.vault_id, 'utf-8', errors='strict')
        b_cipher = to_bytes(self.cipher, 'utf-8', errors='strict')
        b_options = pickle.dumps(self.options)

        header_parts = [self.b_HEADER, b_version, b_cipher, b_options]

        if b_version != b'1.1' and b_vault_id:
            header_parts.append(b_vault_id)

        header = b';'.join(header_parts)

        # compose envelope
        b_envelope = [header]
        b_envelope += [self.vaulted[i:i + 80] for i in range(0, len(self.vaulted), 80)]
        b_envelope += [b'']

        return b'\n'.join(b_envelope)

    @classmethod
    def from_envelope(cls, b_envelope: bytes, default_vault_id: str | None = None, filename: t.AnyStr | None = None) -> t.Self:
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

            b_tmpdata = b_envelope.splitlines()
            b_tmpheader = b_tmpdata[0].strip().split(b';')

            b_vaultedtext = b''.join(b_tmpdata[1:])

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

        v = Vault(str(b_cipher), str(b_version), vault_id, options, filename)
        v.vaulted = b_vaultedtext

        return v


# option: 2, class per version
class Vault_1_1(Vault):
    HEADER_LENGTH = 3
    CIPHER_ALLOWLIST = frozenset(('AES256',))
    CIPHER_WRITE_ALLOWLIST = frozenset(('AES256',))


class Vault_1_2(Vault_1_1):
    HEADER_LENGTH = 4


class Vault_1_3(Vault):
    HEADER_LENGTH = 5
    CIPHER_ALLOWLIST = frozenset(('AES256', 'AES256v2'))
    CIPHER_WRITE_ALLOWLIST = frozenset(('AES256v2',))


class Version():
    ''' TODO: placeholder till i find alt to packaging '''
    pass


def is_vault(data: t.AnyStr) -> bool:
    """ Test if this is vault encrypted data blob

    :arg data: a byte or text string to test whether it is recognized as vault
        encrypted data
    :returns: True if it is recognized.  Otherwise, False.
    """
    try:
        # Make sure we have a byte string and that it only contains ascii bytes.
        b_data = to_bytes(to_text(data, encoding='ascii', errors='strict', nonstring='strict'), encoding='ascii', errors='strict')
    except (UnicodeError, TypeError):
        # The vault format is pure ascii so if we failed to encode to bytes
        # via ascii we know that this is not vault data.
        # Similarly, if it's not a string, it's not vault data
        return False

    return b_data.startswith(Vault.b_HEADER)


# TODO: deprecate is_encrypted, we specifically look for vaults
is_encrypted = is_vault


def is_vault_file(file_obj: t.IO[t.AnyStr], start_pos: int = 0, count: int = len(Vault.b_HEADER)):
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
        return is_vault(file_obj.read(count))

    finally:
        file_obj.seek(current_position)


# TODO: deprecate is_encrypted_file, we specifically look for vaults
is_encrypted_file = is_vault_file
