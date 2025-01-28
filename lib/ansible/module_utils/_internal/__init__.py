from __future__ import annotations

import typing as t

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
