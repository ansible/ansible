# Copyright: (c) 2018, Sviatoslav Sydorenko <ssydoren@redhat.com>
# Copyright: (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collection of low-level utility functions."""

from __future__ import annotations

import collections.abc as _c
from contextlib import suppress as _suppress

import ansible.module_utils.compat.typing as _t


class ImmutableDict(_c.Hashable, _c.Mapping):
    """Dictionary that cannot be updated"""
    def __init__(self, *args, **kwargs) -> None:
        self._store: dict[_c.Hashable, _t.Any] = dict(*args, **kwargs)

    def __getitem__(self, key: _c.Hashable) -> _t.Any:
        return self._store[key]

    def __iter__(self) -> _c.Iterator:
        return self._store.__iter__()

    def __len__(self) -> int:
        return self._store.__len__()

    def __hash__(self) -> int:
        return hash(frozenset(self.items()))

    def __eq__(self, other: _t.Any) -> bool:
        try:
            if self.__hash__() == hash(other):
                return True
        except TypeError:
            pass

        return False

    def __repr__(self) -> str:
        return 'ImmutableDict({0})'.format(repr(self._store))

    def union(self, overriding_mapping: _c.Mapping) -> ImmutableDict:
        """
        Create an ImmutableDict as a combination of the original and overriding_mapping

        :arg overriding_mapping: A Mapping of replacement and additional items
        :return: A copy of the ImmutableDict with key-value pairs from the overriding_mapping added

        If any of the keys in overriding_mapping are already present in the original ImmutableDict,
        the overriding_mapping item replaces the one in the original ImmutableDict.
        """
        return ImmutableDict(self._store, **overriding_mapping)

    def difference(self, subtractive_iterable: _c.Iterable) -> ImmutableDict:
        """
        Create an ImmutableDict as a combination of the original minus keys in subtractive_iterable

        :arg subtractive_iterable: Any iterable containing keys that should not be present in the
            new ImmutableDict
        :return: A copy of the ImmutableDict with keys from the subtractive_iterable removed
        """
        remove_keys = frozenset(subtractive_iterable)
        keys = (k for k in self._store.keys() if k not in remove_keys)
        return ImmutableDict((k, self._store[k]) for k in keys)


class OrderedSet(_c.MutableSet):
    def __init__(
            self,
            iterable: _c.Iterable[_c.Hashable] | None = None,
            /
    ) -> None:

        self._data: dict[_c.Hashable, None]
        if iterable is None:
            self._data = {}
        else:
            self._data = dict.fromkeys(iterable)

    def __repr__(self, /) -> str:
        return f'OrderedSet({list(self._data)!r})'

    def __eq__(self, other: _t.Any, /) -> bool:
        if not isinstance(other, OrderedSet):
            return NotImplemented
        return len(self) == len(other) and tuple(self) == tuple(other)

    def __contains__(self, x: _c.Hashable, /) -> bool:
        return x in self._data

    def __iter__(self, /) -> _c.Iterator:
        return self._data.__iter__()

    def __len__(self, /) -> int:
        return self._data.__len__()

    def add(self, value: _c.Hashable, /) -> None:
        self._data[value] = None

    def discard(self, value: _c.Hashable, /) -> None:
        with _suppress(KeyError):
            del self._data[value]

    def clear(self, /) -> None:
        self._data.clear()

    def copy(self, /) -> OrderedSet:
        return OrderedSet(self._data.copy())

    def __and__(self, other: _c.Container, /) -> OrderedSet:
        # overridden, because the ABC produces an arguably unexpected sorting
        return OrderedSet(value for value in self if value in other)

    difference = _c.MutableSet.__sub__
    difference_update = _c.MutableSet.__isub__
    intersection = __and__
    __rand__ = _c.MutableSet.__and__
    intersection_update = _c.MutableSet.__iand__
    issubset = _c.MutableSet.__le__
    issuperset = _c.MutableSet.__ge__
    symmetric_difference = _c.MutableSet.__xor__
    symmetric_difference_update = _c.MutableSet.__ixor__
    union = _c.MutableSet.__or__
    update = _c.MutableSet.__ior__


def is_string(seq: _c.Iterable) -> bool:
    """Identify whether the input has a string-like type (including bytes)."""
    # AnsibleVaultEncryptedUnicode inherits from Sequence, but is expected to be a string like object
    return isinstance(seq, (str, bytes)) or getattr(seq, '__ENCRYPTED__', False)


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
