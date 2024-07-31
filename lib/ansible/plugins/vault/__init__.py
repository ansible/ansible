# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import abc
import functools
import typing as t
import sys

from ansible.errors import AnsibleError
from ansible.parsing.vault import AnsibleVaultPasswordError, VaultSecret
from ansible.plugins import AnsiblePlugin

VaultSecretError = AnsibleVaultPasswordError


class VaultBase(AnsiblePlugin):
    """Base class all vault methods must implement."""

    # Do not add shared code here unless absolutely necessary.
    # Each implementation is intended to be as standalone as possible to ease backporting.

    @staticmethod
    def _import_error(lib, exception) -> t.NoReturn:
        raise AnsibleError(f"Failed to import the required Python library ({lib}) on the controller's Python ({sys.executable}).") from exception

    @classmethod
    def lru_cache(cls, maxsize: int = 128) -> t.Callable:
        """Passthru impl of lru_cache, exposed to derived types for future extensibility (e.g., auto-sync of new worker-sourced entries to controller)."""
        return functools.lru_cache(maxsize=maxsize)

    @abc.abstractmethod
    def encrypt(self, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        """Encrypt the given plaintext using the provided secret and options and return the resulting vaulttext."""

    @abc.abstractmethod
    def decrypt(self, vaulttext: str, secret: VaultSecret) -> bytes:
        """Decrypt the given vaulttext using the provided secret and return the resulting plaintext."""
