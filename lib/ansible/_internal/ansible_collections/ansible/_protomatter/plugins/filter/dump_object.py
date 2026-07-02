from __future__ import annotations

import dataclasses
import typing as t

from ansible.template import accept_args_markers
from ansible._internal._templating._jinja_common import ExceptionMarker


@accept_args_markers
def dump_object(value: t.Any) -> object:
    """Internal filter to convert objects not supported by JSON to types which are."""
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)  # type: ignore[arg-type]

    if isinstance(value, ExceptionMarker):
        return dict(
            exception=value._as_exception(),
        )

    return value


class FilterModule(object):
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(dump_object=dump_object)
