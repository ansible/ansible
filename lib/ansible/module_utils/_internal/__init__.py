from __future__ import annotations

import collections.abc as c

import typing as t


# DTFIX-RELEASE: bikeshed "intermediate"
INTERMEDIATE_MAPPING_TYPES = (c.Mapping,)
"""
Mapping types which are supported for recursion and runtime usage, such as in serialization and templating.
These will be converted to a simple Python `dict` before serialization or storage as a variable.
"""

INTERMEDIATE_ITERABLE_TYPES = (tuple, set, frozenset, c.Sequence)
"""
Iterable types which are supported for recursion and runtime usage, such as in serialization and templating.
These will be converted to a simple Python `list` before serialization or storage as a variable.
CAUTION: Scalar types which are sequences should be excluded when using this.
"""

ITERABLE_SCALARS_NOT_TO_ITERATE_FIXME = (str, bytes)
"""Scalars which are also iterable, and should thus be excluded from iterable checks."""


def is_intermediate_mapping(value: object) -> bool:
    """Returns `True` if `value` is a type supported for projection to a Python `dict`, otherwise returns `False`."""
    # DTFIX-RELEASE: bikeshed name
    return isinstance(value, INTERMEDIATE_MAPPING_TYPES)


def is_intermediate_iterable(value: object) -> bool:
    """Returns `True` if `value` is a type supported for projection to a Python `list`, otherwise returns `False`."""
    # DTFIX-RELEASE: bikeshed name
    return isinstance(value, INTERMEDIATE_ITERABLE_TYPES) and not isinstance(value, ITERABLE_SCALARS_NOT_TO_ITERATE_FIXME)


is_controller: bool = False
"""Set to True automatically when this module is imported into an Ansible controller context."""


def get_controller_serialize_map() -> dict[type, t.Callable]:
    """
    Called to augment serialization maps.
    This implementation is replaced with the one from ansible._internal in controller contexts.
    """
    return {}


def import_controller_module(_module_name: str, /) -> t.Any:
    """
    Called to conditionally import the named module in a controller context, otherwise returns `None`.
    This implementation is replaced with the one from ansible._internal in controller contexts.
    """
    return None
