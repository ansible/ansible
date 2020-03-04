"""Source provider for content which has been installed."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ... import types as t

from . import (
    SourceProvider,
)


class InstalledSource(SourceProvider):
    """Source provider for content which has been installed."""
    sequence = 0  # disable automatic detection

    @staticmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
        return False

    def get_paths(self, path):  # type: (str) -> t.List[str]
        """Return the list of available content paths under the given path."""
        paths = []

        kill_extensions = (
            '.pyc',
            '.pyo',
        )

        for root, _dummy, file_names in os.walk(path):
            rel_root = os.path.relpath(root, path)

            if rel_root == '.':
                rel_root = ''

            paths.extend([os.path.join(rel_root, file_name) for file_name in file_names
                          if not os.path.splitext(file_name)[1] in kill_extensions])

            # NOTE: directory symlinks are ignored as there should be no directory symlinks for an install

        return paths
