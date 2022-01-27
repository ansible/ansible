"""Source provider to use when the layout is unsupported."""
from __future__ import annotations

import typing as t

from . import (
    SourceProvider,
)


class UnsupportedSource(SourceProvider):
    """Source provider to use when the layout is unsupported."""
    sequence = 0  # disable automatic detection

    @staticmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
        return False

    def get_paths(self, path):  # type: (str) -> t.List[str]
        """Return the list of available content paths under the given path."""
        return []
