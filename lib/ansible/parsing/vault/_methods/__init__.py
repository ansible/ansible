# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import abc
import dataclasses
import functools
import typing as t

from .. import VaultSecret


@dataclasses.dataclass
class _NoParams:
    """No options accepted. Any options provided will result in an error."""


class VaultMethodBase:
    """
    Required base class for vault methods.
    This class uses abstract class methods to support static analysis, but does not extend ABCMeta as it has no runtime effect on them.
    """

    # Do not add shared code here unless absolutely necessary.
    # Each implementation is intended to be as standalone as possible to ease backporting.

    @classmethod
    def lru_cache(cls, maxsize: int = 128) -> t.Callable:
        """Passthru impl of lru_cache, exposed to derived types for future extensibility (e.g., auto-sync of new worker-sourced entries to controller)."""
        return functools.lru_cache(maxsize=maxsize)

    @classmethod
    def no_options(cls, func: t.Callable) -> t.Callable:
        """Indicates the decorated method requires an empty options dict."""
        @functools.wraps(func)
        def wrapper(_cls, *, options: dict[str, t.Any], **kwargs) -> str:
            # noinspection PyArgumentList
            _NoParams(**options)  # raise the same error that would occur when using an invalid option for a method which accepts options

            return func(_cls, options=options, **kwargs)

        return wrapper

    @classmethod
    @abc.abstractmethod
    def encrypt(cls, *, plaintext: bytes, secret: VaultSecret, options: dict[str, t.Any]) -> str:
        """Encrypt the given plaintext using the provided secret and options and return the resulting vaulttext."""

    @classmethod
    @abc.abstractmethod
    def decrypt(cls, *, vaulttext: str, secret: VaultSecret) -> bytes:
        """Decrypt the given vaulttext using the provided secret and return the resulting plaintext."""
