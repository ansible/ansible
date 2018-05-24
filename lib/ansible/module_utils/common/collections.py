# Copyright (c), Sviatoslav Sydorenko <ssydoren@redhat.com> 2018
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collection of low-level utility functions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.common._collections_compat import Sequence


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
