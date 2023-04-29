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
from binascii import Error as BinasciiError
from binascii import unhexlify

from ansible import constants as C
from ansible.errors import AnsibleVaultFormatError
from ansible.module_utils.common.text.converters import to_text

b_HEADER = b'$ANSIBLE_VAULT'


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
            msg += f' in {filename}'
        msg += f': {exc}'
        raise AnsibleVaultFormatError(msg)


def _unhexlify(b_data):
    try:
        return unhexlify(b_data)
    except (BinasciiError, TypeError) as exc:
        raise AnsibleVaultFormatError(f'Vault format unhexlify error: {exc}') from exc
