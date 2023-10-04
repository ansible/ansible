# Copyright (c), Sviatoslav Sydorenko <ssydoren@redhat.com> 2018
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collections ABC import shim.

Use `ansible.module_utils.six.moves.collections_abc` instead, which has been available since ansible-core 2.11.
This module exists only for backwards compatibility.
"""

from __future__ import annotations

# Although this was originally intended for internal use only, it has wide adoption in collections.
# This is due in part to sanity tests previously recommending its use over `collections` imports.
from ansible.module_utils.six.moves.collections_abc import (  # pylint: disable=unused-import
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
