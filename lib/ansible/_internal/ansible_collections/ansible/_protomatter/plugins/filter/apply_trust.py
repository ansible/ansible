from __future__ import annotations

import typing as t

from ansible._internal._datatag._tags import TrustedAsTemplate


def apply_trust(value: object) -> object:
    """
    Filter that returns a tagged copy of the input string with TrustedAsTemplate.
    Containers and other non-string values are returned unmodified.
    """
    return TrustedAsTemplate().tag(value) if isinstance(value, str) else value


class FilterModule:
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(apply_trust=apply_trust)
