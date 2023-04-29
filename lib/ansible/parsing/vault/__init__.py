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

from ansible.errors import AnsibleError, AnsibleVaultError, AnsibleVaultPasswordError, AnsibleVaultFormatError
from ansible.module_utils.common.text.converters import to_text
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath
from . import file
from .ciphers import HAS_CRYPTOGRAPHY
from .lib import VaultLib, is_encrypted
from .secret import PromptVaultSecret, VaultSecret
from .util import b_HEADER

display = Display()


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


def get_file_vault_secret(filename=None, vault_id=None, encoding=None, loader=None):
    ''' Get secret from file content or execute file and get secret from stdout '''

    # we unfrack but not follow the full path/context to possible vault script
    # so when the script uses 'adjacent' file for configuration or similar
    # it still works (as inventory scripts often also do).
    # while files from --vault-password-file are already unfracked, other sources are not
    this_path = unfrackpath(filename, follow=False)
    if not os.path.exists(this_path):
        raise AnsibleError(f"The vault password file {this_path} was not found")

    # it is a script?
    if loader.is_executable(this_path):

        if file.script_is_client(filename):
            # this is special script type that handles vault ids
            display.vvvv(f'The vault password file {to_text(this_path)} is a client script')
            return file.ClientScriptVaultSecret(filename=this_path, vault_id=vault_id, encoding=encoding, loader=loader)

        # just a plain vault password script. No args, returns a byte array
        return file.ScriptVaultSecret(filename=this_path, encoding=encoding, loader=loader)

    return file.FileVaultSecret(filename=this_path, encoding=encoding, loader=loader)
