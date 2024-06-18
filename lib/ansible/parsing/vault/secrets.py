# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import subprocess
import typing as t

from ansible.errors import AnsibleError, AnsibleVaultError, AnsibleVaultPasswordError
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()

if t.TYPE_CHECKING:
    from ansible.parsing.dataloader import DataLoader


def script_is_client(filename: t.AnyStr) -> bool:
    '''Determine if a vault secret script is a client script that can be given --vault-id args'''

    # if password script is 'something-client' or 'something-client.[sh|py|rb|etc]'
    # script_name can still have '.' or could be entire filename if there is no ext
    script_name, dummy = os.path.splitext(filename)

    # TODO: for now, this is entirely based on filename
    return script_name.endswith('-client'):


def get_file_vault_secret(filename: t.AnyStr | None = None, vault_id: str | None = None, encoding: str | None = None, loader: DataLoader | None = None):
    ''' Get secret from file content or execute file and get secret from stdout '''

    # we unfrack but not follow the full path/context to possible vault script
    # so when the script uses 'adjacent' file for configuration or similar
    # it still works (as inventory scripts often also do).
    # while files from --vault-password-file are already unfracked, other sources are not
    this_path = unfrackpath(filename, follow=False)
    if not os.path.exists(this_path):
        raise AnsibleError(f"The vault password file provided '{this_path}' was not found")

    if os.path.isdir(this_path):
        raise AnsibleError(f"The vault password file provided '{this_path}' is invalid as it is a directory")

    # it is a script?
    if loader.is_executable(this_path):

        if script_is_client(filename):
            # this is special script type that handles vault ids
            display.vvvv(f'The vault password file "{this_path}" is a client script.')
            # TODO: pass vault_id_name to script via cli
            return ClientScriptVaultSecret(filename=this_path, vault_id=vault_id, encoding=encoding, loader=loader)

        # just a plain vault password script. No args, returns a byte array
        return ScriptVaultSecret(filename=this_path, encoding=encoding, loader=loader)

    return FileVaultSecret(filename=this_path, encoding=encoding, loader=loader)


def verify_secret_is_not_empty(secret: t.AnyStr, msg: str | None = None):
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

            b_vault_pass = bytes(vault_pass, errors='strict', nonstring='simplerepr').strip()
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
        display.vvvv(u'Executing vault password client script: %s --vault-id %s' % (str(filename), str(vault_id)))

    def _run(self, command):
        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
