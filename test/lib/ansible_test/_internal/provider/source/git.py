"""Source provider for a content root managed by git version control."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ... import types as t

from ...git import (
    Git,
)

from ...util import (
    to_bytes,
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

        paths = self.__get_paths(path)

        submodule_paths = git.get_submodule_paths()

        for submodule_path in submodule_paths:
            paths.extend(os.path.join(submodule_path, p) for p in self.__get_paths(os.path.join(path, submodule_path)))

        return paths

    @staticmethod
    def __get_paths(path):  # type: (str) -> t.List[str]
        """Return the list of available content paths under the given path."""
        git = Git(path)
        paths = git.get_file_names(['--cached', '--others', '--exclude-standard'])
        deleted_paths = git.get_file_names(['--deleted'])
        paths = sorted(set(paths) - set(deleted_paths))

        # directory symlinks are reported by git as regular files but they need to be treated as directories
        paths = [path + os.path.sep if os.path.isdir(to_bytes(path)) else path for path in paths]

        return paths
