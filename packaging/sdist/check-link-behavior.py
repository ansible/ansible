#!/usr/bin/env python
"""Checks for link behavior required for sdist to retain symlinks."""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os
import platform
import shutil
import sys
import tempfile


def main():
    """Main program entry point."""
    temp_dir = tempfile.mkdtemp()

    target_path = os.path.join(temp_dir, 'file.txt')
    symlink_path = os.path.join(temp_dir, 'symlink.txt')
    hardlink_path = os.path.join(temp_dir, 'hardlink.txt')

    try:
        with open(target_path, 'w'):
            pass

        os.symlink(target_path, symlink_path)
        os.link(symlink_path, hardlink_path)

        if not os.path.islink(symlink_path):
            abort('Symbolic link not created.')

        if not os.path.islink(hardlink_path):
            # known issue on MacOS (Darwin)
            abort('Hard link of symbolic link created as a regular file.')
    finally:
        shutil.rmtree(temp_dir)


def abort(reason):
    """
    :type reason: str
    """
    sys.exit('ERROR: %s\n'
             'This will prevent symbolic links from being preserved in the resulting tarball.\n'
             'Aborting creation of sdist on platform: %s'
             % (reason, platform.system()))


if __name__ == '__main__':
    main()
