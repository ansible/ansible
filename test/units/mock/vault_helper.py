from __future__ import annotations

from ansible._internal._datatag import _tags
from ansible.module_utils.common.text.converters import to_bytes
from ansible.parsing.vault import VaultSecret, VaultSecretsContext, VaultLib, EncryptedString


class TextVaultSecret(VaultSecret):
    """A secret piece of text. ie, a password. Tracks text encoding.

    The text encoding of the text may not be the default text encoding so
    we keep track of the encoding so we encode it to the same bytes."""

    def __init__(self, text, encoding=None, errors=None, _bytes=None):
        super(TextVaultSecret, self).__init__()
        self.text = text
        self.encoding = encoding or 'utf-8'
        self._bytes = _bytes
        self.errors = errors or 'strict'

    @property
    def bytes(self):
        """The text encoded with encoding, unless we specifically set _bytes."""
        return self._bytes or to_bytes(self.text, encoding=self.encoding, errors=self.errors)


class VaultTestHelper:
    @classmethod
    def make_vault_ciphertext(cls, plaintext: str) -> str:
        """Creates an `EncryptedString` from the first secret in the active VaultSecretsContext."""
        secrets = VaultSecretsContext.current().secrets
        vl = VaultLib(secrets)

        return vl.encrypt(plaintext, secrets[0][1]).decode()

    @classmethod
    def make_encrypted_string(cls, plaintext: str) -> EncryptedString:
        """Creates an `EncryptedString` from the first secret in the active VaultSecretsContext."""
        return _tags.Origin(path="/tmp/sometest", line_num=42, col_num=42).tag(EncryptedString(ciphertext=cls.make_vault_ciphertext(plaintext)))
