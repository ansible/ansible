# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import abc
import functools
import typing as t

from .. import AnsibleVaultPasswordError, VaultSecret

VaultSecretError = AnsibleVaultPasswordError


class VaultMethodBase:
    """Base class all vault methods must implement."""

    # Do not add shared code here unless absolutely necessary.
    # Each implementation is intended to be as standalone as possible to ease backporting.

    @classmethod
    def lru_cache(cls, maxsize: int = 128) -> t.Callable:
        """Passthru impl of lru_cache, exposed to derived types for future extensibility (e.g., auto-sync of new worker-sourced entries to controller)."""
        return functools.lru_cache(maxsize=maxsize)

    @classmethod
    @abc.abstractmethod
    def encrypt(cls, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        """Encrypt the given plaintext using the provided secret and options and return the resulting vaulttext."""

    @classmethod
    @abc.abstractmethod
    def decrypt(cls, vaulttext: str, secret: VaultSecret) -> bytes:
        """Decrypt the given vaulttext using the provided secret and return the resulting plaintext."""
