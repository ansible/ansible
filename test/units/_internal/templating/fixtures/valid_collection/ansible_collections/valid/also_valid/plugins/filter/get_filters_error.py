from __future__ import annotations

import typing as t


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        raise NotImplementedError()  # this should generate a warning, but shouldn't prevent other plugins from working
