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

from ansible.errors import AnsibleVaultError
from ansible.module_utils._text import to_text, to_bytes

b_HEADER = b'$ANSIBLE_VAULT'


def format_envelope(b_ciphertext, cipher_name, b_version):
    """ Add header and format to 80 columns

        :arg b_vaulttext: the encrypted and hexlified data as a byte string
        :returns: a byte str that should be dumped into a file.  It's
            formatted to 80 char columns and has the header prepended
    """

    if not cipher_name:
        raise AnsibleVaultError("the cipher must be set before adding a header")

    header = b';'.join([b_HEADER, b_version,
                        to_bytes(cipher_name, 'utf-8', errors='strict')])
    b_vaulttext = [header]
    b_vaulttext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
    b_vaulttext += [b'']
    b_vaulttext = b'\n'.join(b_vaulttext)

    return b_vaulttext


def is_vault_envelope(data):
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


def parse_envelope(b_vaulttext):
    """Retrieve information about the Vault and clean the data

    When data is saved, it has a header prepended and is formatted into 80
    character lines.  This method extracts the information from the header
    and then removes the header and the inserted newlines.  The string returned
    is suitable for processing by the Cipher classes.

    :arg b_vaulttext: byte str containing the data from a save file
    :returns: a 3 item tuple of
        a byte str suitable for passing to a Cipher class's
        decrypt() function.
    """
    # used by decrypt
    if not is_vault_envelope(b_vaulttext):
        msg = "input is not vault encrypted data"
        raise AnsibleVaultError(msg)

    b_tmpdata = b_vaulttext.split(b'\n')
    b_tmpheader = b_tmpdata[0].strip().split(b';')

    b_version = b_tmpheader[1].strip()
    cipher_name = to_text(b_tmpheader[2].strip())
    b_ciphertext = b''.join(b_tmpdata[1:])

    return b_ciphertext, cipher_name, b_version
