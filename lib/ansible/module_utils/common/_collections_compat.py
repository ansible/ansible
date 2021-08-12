# Copyright (c), Sviatoslav Sydorenko <ssydoren@redhat.com> 2018
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collections ABC import shim.

This module is intended only for internal use.
It will go away once the bundled copy of six includes equivalent functionality.
Third parties should not use this.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    """Python 3.3+ branch."""
    from collections.abc import (
        MappingView,
        ItemsView,
        KeysView,
        ValuesView,
        Mapping, MutableMapping,
        Sequence, MutableSequence,
        Set, MutableSet,
        Container,
        Hashable,
        Sized,
        Callable,
        Iterable,
        Iterator,
    )
except ImportError:
    """Use old lib location under 2.6-3.2."""
    from collections import (  # pylint: disable=deprecated-class
        MappingView,
        ItemsView,
        KeysView,
        ValuesView,
        Mapping, MutableMapping,
        Sequence, MutableSequence,
        Set, MutableSet,
        Container,
        Hashable,
        Sized,
        Callable,
        Iterable,
        Iterator,
    )
