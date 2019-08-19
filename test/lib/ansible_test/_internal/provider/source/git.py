"""Source provider for a content root managed by git version control."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ... import types as t

from ...git import (
    Git,
)

from . import (
    SourceProvider,
)


class GitSource(SourceProvider):
    """Source provider for a content root managed by git version control."""
    @staticmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
        return os.path.exists(os.path.join(path, '.git'))

    def get_paths(self, path):  # type: (str) -> t.List[str]
        """Return the list of available content paths under the given path."""
        git = Git(path)

        paths = git.get_file_names(['--cached', '--others', '--exclude-standard'])
        deleted_paths = git.get_file_names(['--deleted'])
        paths = sorted(set(paths) - set(deleted_paths))

        return paths
