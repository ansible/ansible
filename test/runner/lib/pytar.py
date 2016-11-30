"""Python native TGZ creation."""

from __future__ import absolute_import, print_function

import tarfile
import os

# improve performance by disabling uid/gid lookups
tarfile.pwd = None
tarfile.grp = None

# To reduce archive time and size, ignore non-versioned files which are large or numerous.
# Also ignore miscellaneous git related files since the .git directory is ignored.

IGNORE_DIRS = (
    '.tox',
    '.git',
    '.idea',
    '__pycache__',
    'ansible.egg-info',
)

IGNORE_FILES = (
    '.gitignore',
    '.gitdir',
)

IGNORE_EXTENSIONS = (
    '.pyc',
    '.retry',
)


def ignore(item):
    """
    :type item: tarfile.TarInfo
    :rtype: tarfile.TarInfo | None
    """
    filename = os.path.basename(item.path)
    name, ext = os.path.splitext(filename)
    dirs = os.path.split(item.path)

    if not item.isdir():
        if item.path.startswith('./test/results/'):
            return None

        if item.path.startswith('./docsite/') and filename.endswith('_module.rst'):
            return None

    if name in IGNORE_FILES:
        return None

    if ext in IGNORE_EXTENSIONS:
        return None

    if any(d in IGNORE_DIRS for d in dirs):
        return None

    return item


def create_tarfile(dst_path, src_path, tar_filter):
    """
    :type dst_path: str
    :type src_path: str
    :type tar_filter: (tarfile.TarInfo) -> tarfile.TarInfo | None
    """
    with tarfile.TarFile.gzopen(dst_path, mode='w', compresslevel=4) as tar:
        tar.add(src_path, filter=tar_filter)
