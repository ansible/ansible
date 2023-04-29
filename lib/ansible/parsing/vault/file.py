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
import os
import subprocess

from ansible.errors import AnsibleError, AnsibleVaultError
from ansible.module_utils.common.text.converters import to_text
from ansible.utils.display import Display
from .secret import VaultSecret, verify_secret_is_not_empty

display = Display()


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
            raise AnsibleError(f"Could not read vault password file {filename}: {e}") from e

        b_vault_data, dummy = self.loader._decrypt_if_vault_data(vault_pass, filename)

        vault_pass = b_vault_data.strip(b'\r\n')
        verify_secret_is_not_empty(vault_pass, msg=f'Invalid vault password was provided from file ({filename})')

        return vault_pass

    def __repr__(self):
        if self.filename:
            return f"{self.__class__.__name__}(filename='{self.filename}')"
        return f"{self.__class__.__name__}()"


class ScriptVaultSecret(FileVaultSecret):
    def _read_file(self, filename):
        if not self.loader.is_executable(filename):
            raise AnsibleVaultError(f"The vault password script {filename} was not executable")

        command = self._build_command()

        stdout, stderr, p = self._run(command)

        self._check_results(stdout, stderr, p)

        vault_pass = stdout.strip(b'\r\n')

        verify_secret_is_not_empty(vault_pass, msg=f'Invalid vault password was provided from script ({filename})')

        return vault_pass

    def _run(self, command):
        try:
            # STDERR not captured to make it easier for users to prompt for input in their scripts
            p = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError(f"Problem running vault password script {self.filename} ({e})."
                               " If this is not a script, remove the executable bit from the file.") from e

        stdout, stderr = p.communicate()
        return stdout, stderr, p

    def _check_results(self, stdout, stderr, popen):
        if popen.returncode != 0:
            raise AnsibleError(
                f"Vault password script {self.filename} returned non-zero ({popen.returncode}): {stderr}")

    def _build_command(self):
        return [self.filename]


class ClientScriptVaultSecret(ScriptVaultSecret):
    VAULT_ID_UNKNOWN_RC = 2

    def __init__(self, filename=None, encoding=None, loader=None, vault_id=None):
        super(ClientScriptVaultSecret, self).__init__(filename=filename, encoding=encoding, loader=loader)
        self._vault_id = vault_id
        display.vvvv(f'Executing vault password client script: {to_text(filename)} --vault-id {to_text(vault_id)}')

    def _run(self, command):
        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError(f"Problem running vault password client script {self.filename} ({e})."
                               " If this is not a script, remove the executable bit from the file.") from e

        stdout, stderr = p.communicate()
        return stdout, stderr, p

    def _check_results(self, stdout, stderr, popen):
        if popen.returncode == self.VAULT_ID_UNKNOWN_RC:
            raise AnsibleError(
                f'Vault password client script {self.filename} '
                f'did not find a secret for vault-id={self._vault_id}: {stderr}')

        if popen.returncode != 0:
            raise AnsibleError(
                f"Vault password client script {self.filename} returned non-zero ({popen.returncode}) "
                f"when getting secret for vault-id={self._vault_id}: {stderr}")

    def _build_command(self):
        command = [self.filename]
        if self._vault_id:
            command.extend(['--vault-id', self._vault_id])

        return command

    def __repr__(self):
        if self.filename:
            return f"{self.__class__.__name__}(filename='{self.filename}', vault_id='{self._vault_id}')"
        return f"{self.__class__.__name__}()"


def script_is_client(filename):
    '''Determine if a vault secret script is a client script that can be given --vault-id args'''

    # if password script is 'something-client' or 'something-client.[sh|py|rb|etc]'
    # script_name can still have '.' or could be entire filename if there is no ext
    script_name, dummy = os.path.splitext(filename)

    # TODO: for now, this is entirely based on filename
    if script_name.endswith('-client'):
        return True

    return False
