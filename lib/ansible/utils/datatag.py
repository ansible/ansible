from __future__ import annotations as _annotations

import io as _io
import typing as _t

from .._internal._datatag import _tags, _wrappers
from ..module_utils import datatag as _datatag

_T = _t.TypeVar('_T', bound=str | _io.IOBase | _t.TextIO | _t.BinaryIO)


def trust_value(value: _T) -> _T:
    """
    Return `value` tagged as trusted for templating.
    Raises a `TypeError` if `value` is not a supported type.
    """
    if isinstance(value, str):
        return _tags.TrustedAsTemplate().tag(value)  # type: ignore[return-value]

    if isinstance(value, _io.IOBase):  # covers TextIO and BinaryIO at runtime, but type checking disagrees
        return _wrappers.TaggedStreamWrapper(value, _tags.TrustedAsTemplate())

    raise TypeError(f"Trust cannot be applied to {_datatag.native_type_name(value)}, only to 'str' or 'IOBase'.")
