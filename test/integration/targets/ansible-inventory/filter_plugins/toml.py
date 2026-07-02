from __future__ import annotations

import tomllib
import typing as t


def from_toml(o) -> t.Any:
    return tomllib.loads(o)


class FilterModule:
    def filters(self) -> dict[str, t.Any]:
        return dict(
            from_toml=from_toml,
        )
