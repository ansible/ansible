from __future__ import annotations

import typing as t


def also_also_valid(*args, **kwargs) -> list:
    return []


def runtime_error(*args, **kwargs) -> t.NoReturn:
    raise NotImplementedError()


class Bomb:
    @property
    def accept_args_markers(self) -> t.NoReturn:
        raise NotImplementedError()


class FilterModule:
    def filters(self) -> dict[str, t.Any]:
        return dict(
            also_also_valid=also_also_valid,
            runtime_error=runtime_error,
            load_error=Bomb(),
        )
