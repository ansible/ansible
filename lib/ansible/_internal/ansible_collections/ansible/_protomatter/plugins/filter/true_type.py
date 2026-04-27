from __future__ import annotations

import typing as t

from ansible.template import accept_args_markers


@accept_args_markers
def true_type(obj: object) -> str:
    """Internal filter to show the true type name of the given object, not just the base type name like the `debug` filter."""
    return obj.__class__.__name__


class FilterModule(object):
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(true_type=true_type)
