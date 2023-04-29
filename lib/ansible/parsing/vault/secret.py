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
from ansible.errors import AnsibleError, AnsibleVaultError, AnsibleVaultPasswordError
from ansible.module_utils.common.text.converters import to_bytes
from ansible.utils.display import Display

display = Display()


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
                raise AnsibleVaultError(f"EOFError (ctrl-d) on prompt for ({self.vault_id})")

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


def verify_secret_is_not_empty(secret, msg=None):
    '''Check the secret against minimal requirements.

    Raises: AnsibleVaultPasswordError if the password does not meet requirements.

    Currently, only requirement is that the password is not None or an empty string.
    '''
    msg = msg or 'Invalid vault password was provided'
    if not secret:
        raise AnsibleVaultPasswordError(msg)
