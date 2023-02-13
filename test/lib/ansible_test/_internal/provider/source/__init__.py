"""Common code for source providers."""
from __future__ import annotations

import abc

from .. import (
    PathProvider,
)


class SourceProvider(PathProvider):
    """Base class for source providers."""

    @abc.abstractmethod
    def get_paths(self, path: str) -> list[str]:
        """Return the list of available content paths under the given path."""
