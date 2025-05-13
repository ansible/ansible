from __future__ import annotations

import typing as t

from ansible._internal._templating._engine import _finalize_template_result, FinalizeMode


def finalize(value: t.Any) -> t.Any:
    """Perform an explicit top-level template finalize operation on the supplied value."""
    return _finalize_template_result(value, mode=FinalizeMode.TOP_LEVEL)


class FilterModule:
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(finalize=finalize)
