from __future__ import annotations

import typing as t

from ansible.utils.datatag.tags import NotATemplate, TrustedAsTemplate


def apply_trust(value: t.Any) -> t.Any:
    """
    Filter that returns a tagged copy of the input string with TrustedAsTemplate and removes NotATemplate (if present).
    Containers and other non-string values are returned unmodified.
    """
    return NotATemplate.untag(TrustedAsTemplate().tag(value)) if isinstance(value, str) else value


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        return dict(apply_trust=apply_trust)
