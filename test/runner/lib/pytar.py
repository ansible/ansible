"""Python native TGZ creation."""

from __future__ import absolute_import, print_function

import abc
import tarfile
import os

from lib.util import (
    display,
    ABC,
)

from lib.constants import (
    TIMEOUT_PATH,
)

# improve performance by disabling uid/gid lookups
tarfile.pwd = None
tarfile.grp = None


class TarFilter(ABC):
    """Filter to use when creating a tar file."""
    @abc.abstractmethod
    def ignore(self, item):
        """
        :type item: tarfile.TarInfo
        :rtype: tarfile.TarInfo | None
        """
        pass


class DefaultTarFilter(TarFilter):
    """
    To reduce archive time and size, ignore non-versioned files which are large or numerous.
    Also ignore miscellaneous git related files since the .git directory is ignored.
    """
    def __init__(self):
        self.ignore_dirs = (
            '.tox',
            '.git',
            '.idea',
            '.pytest_cache',
            '__pycache__',
            'ansible.egg-info',
        )

        self.ignore_files = (
            '.gitignore',
            '.gitdir',
            TIMEOUT_PATH,
        )

        self.ignore_extensions = (
            '.pyc',
            '.retry',
        )

    def ignore(self, item):
        """
        :type item: tarfile.TarInfo
        :rtype: tarfile.TarInfo | None
        """
        filename = os.path.basename(item.path)
        ext = os.path.splitext(filename)[1]
        dirs = os.path.split(item.path)

        if not item.isdir():
            if item.path.startswith('./test/results/'):
                return None

            if item.path.startswith('./docs/docsite/_build/'):
                return None

        if filename in self.ignore_files:
            return None

        if ext in self.ignore_extensions:
            return None

        if any(d in self.ignore_dirs for d in dirs):
            return None

        return item


class AllowGitTarFilter(DefaultTarFilter):
    """
    Filter that allows git related files normally excluded by the default tar filter.
    """
    def __init__(self):
        super(AllowGitTarFilter, self).__init__()

        self.ignore_dirs = tuple(d for d in self.ignore_dirs if not d.startswith('.git'))
        self.ignore_files = tuple(f for f in self.ignore_files if not f.startswith('.git'))


def create_tarfile(dst_path, src_path, tar_filter):
    """
    :type dst_path: str
    :type src_path: str
    :type tar_filter: TarFilter
    """
    display.info('Creating a compressed tar archive of path: %s' % src_path, verbosity=1)

    with tarfile.TarFile.open(dst_path, mode='w:gz', compresslevel=4, format=tarfile.GNU_FORMAT) as tar:
        tar.add(src_path, filter=tar_filter.ignore)

    display.info('Resulting archive is %d bytes.' % os.path.getsize(dst_path), verbosity=1)
