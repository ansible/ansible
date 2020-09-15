"""Common code for source providers."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc

from ... import types as t

from .. import (
    PathProvider,
)


class SourceProvider(PathProvider):
    """Base class for source providers."""
    @abc.abstractmethod
    def get_paths(self, path):  # type: (str) -> t.List[str]
        """Return the list of available content paths under the given path."""
