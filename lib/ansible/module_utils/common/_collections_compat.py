# Copyright (c), Sviatoslav Sydorenko <ssydoren@redhat.com> 2018
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Collections ABC import shim.

Use `collections.abc` instead.
This module exists only for backwards compatibility.
"""

from __future__ import annotations

# Although this was originally intended for internal use only, it has wide adoption in collections.
# This is due in part to sanity tests previously recommending its use over `collections` imports.
from collections.abc import (  # pylint: disable=unused-import
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

from ansible.module_utils.common import warnings as _warnings


_warnings.deprecate(
    msg="The `ansible.module_utils.common._collections_compat` module is deprecated.",
    help_text="Use `collections.abc` from the Python standard library instead.",
    version="2.24",
)
