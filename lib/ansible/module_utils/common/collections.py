# Copyright: (c) 2018, Sviatoslav Sydorenko <ssydoren@redhat.com>
# Copyright: (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collection of low-level utility functions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.common._collections_compat import Hashable, Mapping, Sequence


class ImmutableDict(Hashable, Mapping):
    """Dictionary that cannot be updated"""
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self._store[key]

    def __iter__(self):
        return self._store.__iter__()

    def __len__(self):
        return self._store.__len__()

    def __hash__(self):
        return hash(frozenset(self.items()))

    def __repr__(self):
        return 'ImmutableDict({0})'.format(repr(self._store))

    def union(self, overriding_mapping):
        """
        Create an ImmutableDict as a combination of the original and overriding_mapping

        :arg overriding_mapping: A Mapping of replacement and additional items
        :return: A copy of the ImmutableDict with key-value pairs from the overriding_mapping added

        If any of the keys in overriding_mapping are already present in the original ImmutableDict,
        the overriding_mapping item replaces the one in the original ImmutableDict.
        """
        return ImmutableDict(self._store, **overriding_mapping)

    def difference(self, subtractive_iterable):
        """
        Create an ImmutableDict as a combination of the original minus keys in subtractive_iterable

        :arg subtractive_iterable: Any iterable containing keys that should not be present in the
            new ImmutableDict
        :return: A copy of the ImmutableDict with keys from the subtractive_iterable removed
        """
        remove_keys = frozenset(subtractive_iterable)
        keys = (k for k in self._store.keys() if k not in remove_keys)
        return ImmutableDict((k, self._store[k]) for k in keys)


def is_string(seq):
    """Identify whether the input has a string-like type (inclding bytes)."""
    return isinstance(seq, (text_type, binary_type))


def is_iterable(seq, include_strings=False):
    """Identify whether the input is an iterable."""
    if not include_strings and is_string(seq):
        return False

    try:
        iter(seq)
        return True
    except TypeError:
        return False


def is_sequence(seq, include_strings=False):
    """Identify whether the input is a sequence.

    Strings and bytes are not sequences here,
    unless ``include_string`` is ``True``.

    Non-indexable things are never of a sequence type.
    """
    if not include_strings and is_string(seq):
        return False

    return isinstance(seq, Sequence)


def count(seq):
    """Returns a dictionary with the number of appearances of each element of the iterable.

    Resembles the collections.Counter class functionality. It is meant to be used when the
    code is run on Python 2.6.* where collections.Counter is not available. It should be
    deprecated and replaced when support for Python < 2.7 is dropped.
    """
    if not is_iterable(seq):
        raise Exception('Argument provided  is not an iterable')
    counters = dict()
    for elem in seq:
        counters[elem] = counters.get(elem, 0) + 1
    return counters
