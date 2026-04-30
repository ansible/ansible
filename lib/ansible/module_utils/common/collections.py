# Copyright: (c) 2018, Sviatoslav Sydorenko <ssydoren@redhat.com>
# Copyright: (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collection of low-level utility functions."""

from __future__ import annotations

import collections.abc as _c
import typing as _t

from ansible.module_utils._internal import _no_six
from ansible.module_utils.common import warnings as _warnings

_KT = _t.TypeVar('_KT', bound=_c.Hashable)
_VT = _t.TypeVar('_VT')
_T = _t.TypeVar('_T', bound=_c.Hashable)


class ImmutableDict(_c.Hashable, _c.Mapping[_KT, _VT], _t.Generic[_KT, _VT]):
    """Dictionary that cannot be updated"""
    def __init__(
        self,
        *args: _c.Mapping[_KT, _VT] | _c.Iterable[tuple[_KT, _VT]],
        **kwargs: _VT,
    ) -> None:
        self._store: dict[_KT, _VT] = dict(*args) if args else {}
        if kwargs:
            self._store.update(_t.cast(_c.Mapping[_KT, _VT], kwargs))

    def __getitem__(self, key: _KT) -> _VT:
        return self._store[key]

    def __iter__(self) -> _c.Iterator[_KT]:
        return self._store.__iter__()

    def __len__(self) -> int:
        return self._store.__len__()

    def __hash__(self) -> int:
        return hash(frozenset(self.items()))

    def __eq__(self, other: object) -> bool:
        try:
            if self.__hash__() == hash(other):
                return True
        except TypeError:
            pass

        return False

    def __repr__(self) -> str:
        return 'ImmutableDict({0})'.format(repr(self._store))

    def union(self, overriding_mapping: _c.Mapping[_KT, _VT]) -> ImmutableDict[_KT, _VT]:
        """
        Create an ImmutableDict as a combination of the original and overriding_mapping

        :arg overriding_mapping: A Mapping of replacement and additional items
        :return: A copy of the ImmutableDict with key-value pairs from the overriding_mapping added

        If any of the keys in overriding_mapping are already present in the original ImmutableDict,
        the overriding_mapping item replaces the one in the original ImmutableDict.
        """
        result = dict(self._store)
        result.update(overriding_mapping)
        return ImmutableDict(result)

    def difference(self, subtractive_iterable: _c.Iterable) -> ImmutableDict[_KT, _VT]:
        """
        Create an ImmutableDict as a combination of the original minus keys in subtractive_iterable

        :arg subtractive_iterable: Any iterable containing keys that should not be present in the
            new ImmutableDict
        :return: A copy of the ImmutableDict with keys from the subtractive_iterable removed
        """
        remove_keys = frozenset(subtractive_iterable)
        keys = (k for k in self._store.keys() if k not in remove_keys)
        return ImmutableDict((k, self._store[k]) for k in keys)


class OrderedSet(_c.MutableSet[_T], _t.Generic[_T]):
    def __init__(
            self,
            iterable: _c.Iterable[_T] | None = None,
            /
    ) -> None:

        self._data: dict[_T, None] = dict.fromkeys(iterable or ())

    def __repr__(self, /) -> str:
        return f'OrderedSet({list(self)!r})'

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, OrderedSet):
            return NotImplemented
        return tuple(self._data) == tuple(other._data)

    def __contains__(self, x: object, /) -> bool:
        return x in self._data

    def __iter__(self, /) -> _c.Iterator[_T]:
        return self._data.__iter__()

    def __len__(self, /) -> int:
        return self._data.__len__()

    def add(self, value: _T) -> None:
        self._data[value] = None

    def discard(self, value: _T) -> None:
        self._data.pop(value, None)

    def clear(self) -> None:
        self._data.clear()

    def copy(self) -> OrderedSet[_T]:
        result: OrderedSet[_T] = OrderedSet()
        result._data = self._data.copy()
        return result

    def __and__(self, other: _c.Container, /) -> OrderedSet[_T]:
        # overridden, because the ABC produces an arguably unexpected sorting
        return OrderedSet(value for value in self if value in other)

    def __sub__(self, other: _c.Container, /) -> OrderedSet[_T]:
        return OrderedSet(value for value in self if value not in other)

    def __or__(self, other: _c.Set[_T], /) -> OrderedSet[_T]:  # type: ignore[override]
        result = self.copy()
        for value in other:
            result._data[value] = None
        return result

    def __xor__(self, other: _c.Set[_T], /) -> OrderedSet[_T]:  # type: ignore[override]
        result = self.copy()
        for value in other:
            if value in result._data:
                del result._data[value]
            else:
                result._data[value] = None
        return result

    def __rsub__(self, other: _c.Iterable[_T], /) -> OrderedSet[_T]:
        return OrderedSet(other).__sub__(self)

    def __rxor__(self, other: _c.Iterable[_T], /) -> OrderedSet[_T]:
        return OrderedSet(other).__xor__(self)

    difference = __sub__
    difference_update = _c.MutableSet.__isub__
    intersection = __and__
    __rand__ = __and__
    __ror__ = __or__
    intersection_update = _c.MutableSet.__iand__
    issubset = _c.MutableSet.__le__
    issuperset = _c.MutableSet.__ge__
    symmetric_difference = __xor__
    symmetric_difference_update = _c.MutableSet.__ixor__
    union = __or__
    update = _c.MutableSet.__ior__


def is_string(seq: _c.Iterable) -> bool:
    """Identify whether the input has a string-like type (including bytes)."""
    return isinstance(seq, (str, bytes))


def is_iterable(seq: _c.Iterable, include_strings: bool = False) -> bool:
    """Identify whether the input is an iterable."""
    if not include_strings and is_string(seq):
        return False

    try:
        iter(seq)
        return True
    except TypeError:
        return False


def is_sequence(seq: _c.Iterable, include_strings: bool = False) -> bool:
    """Identify whether the input is a sequence.

    Strings and bytes are not sequences here,
    unless ``include_string`` is ``True``.

    Non-indexable things are never of a sequence type.
    """
    if not include_strings and is_string(seq):
        return False

    return isinstance(seq, _c.Sequence)


def count(seq: _c.Iterable) -> dict[_c.Hashable, int]:
    """Returns a dictionary with the number of appearances of each element of the iterable.

    Resembles the collections.Counter class functionality. It is meant to be used when the
    code is run on Python 2.6.* where collections.Counter is not available. It should be
    deprecated and replaced when support for Python < 2.7 is dropped.
    """
    _warnings.deprecate(
        msg="The `ansible.module_utils.common.collections.count` function is deprecated.",
        version="2.23",
        help_text="Use `collections.Counter` from the Python standard library instead.",
    )
    if not is_iterable(seq):
        raise Exception('Argument provided  is not an iterable')
    counters: dict[_c.Hashable, int] = {}
    for elem in seq:
        counters[elem] = counters.get(elem, 0) + 1
    return counters


Hashable = _c.Hashable
Mapping = _c.Mapping
MutableMapping = _c.MutableMapping
Sequence = _c.Sequence


def __getattr__(importable_name):
    return _no_six.deprecate(importable_name, __name__, "binary_type", "text_type")
