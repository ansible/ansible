from __future__ import annotations

import dataclasses
import typing as t


def dump_object(value: t.Any) -> object:
    """Internal filter to convert objects not supported by JSON to types which are."""
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)  # type: ignore[call-overload]

    return value


class FilterModule(object):
    def filters(self) -> dict[str, t.Callable]:
        return dict(dump_object=dump_object)
