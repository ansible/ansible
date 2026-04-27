# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: This implementation of the collection loader is used by ansible-test.
#          Because of this, it must be compatible with all Python versions supported on the controller or remote.

from __future__ import annotations

import typing as t


@t.runtime_checkable
class _EncryptedStringProtocol(t.Protocol):
    """Protocol representing an `EncryptedString`, since it cannot be imported here."""

    # DTFIX-FUTURE: collapse this with the one in config, once we can

    def _decrypt(self) -> str: ...


def _to_text(value: str | bytes | _EncryptedStringProtocol | None, strict: bool = False) -> str | None:
    """Internal implementation to keep collection loader standalone."""
    # FUTURE: remove this method when _to_bytes is removed

    if value is None:
        return None

    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        return value.decode(errors='strict' if strict else 'surrogateescape')

    if isinstance(value, _EncryptedStringProtocol):
        return value._decrypt()

    raise TypeError(f'unsupported type {type(value)}')


def _to_bytes(value: str | bytes | _EncryptedStringProtocol | None, strict: bool = False) -> bytes | None:
    """Internal implementation to keep collection loader standalone."""
    # FUTURE: remove this method and rely on automatic str -> bytes conversions of filesystem methods instead

    if value is None:
        return None

    if isinstance(value, bytes):
        return value

    if isinstance(value, str):
        return value.encode(errors='strict' if strict else 'surrogateescape')

    if isinstance(value, _EncryptedStringProtocol):
        return value._decrypt().encode(errors='strict' if strict else 'surrogateescape')

    raise TypeError(f'unsupported type {type(value)}')


def resource_from_fqcr(ref):
    """
    Return resource from a fully-qualified collection reference,
    or from a simple resource name.
    For fully-qualified collection references, this is equivalent to
    ``AnsibleCollectionRef.from_fqcr(ref).resource``.
    :param ref: collection reference to parse
    :return: the resource as a unicode string
    """
    ref = _to_text(ref, strict=True)
    return ref.split(u'.')[-1]


# FIXME: decide what of this we want to actually be public/toplevel, put other stuff on a utility class?
from ._collection_config import AnsibleCollectionConfig
from ._collection_finder import AnsibleCollectionRef
