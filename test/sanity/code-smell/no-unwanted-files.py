#!/usr/bin/env python
"""Prevent unwanted files from being added to the source tree."""
import os
import sys


def main():
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    allowed_extensions = (
        '.cs',
        '.ps1',
        '.psm1',
        '.py',
    )

    skip = (
        # allowed special cases
        'lib/ansible/config/base.yml',
        'lib/ansible/config/module_defaults.yml',
    )

    skip_directories = (
        'lib/ansible.egg-info/',
        'lib/ansible/galaxy/data/',
    )

    for path in paths:
        if path in skip:
            continue

        if any(path.startswith(skip_directory) for skip_directory in skip_directories):
            continue

        if path.startswith('lib/') and not path.startswith('lib/ansible/'):
            print('%s: all "lib" content must reside in the "lib/ansible" directory' % path)
            continue

        ext = os.path.splitext(path)[1]

        if ext not in allowed_extensions:
            print('%s: extension must be one of: %s' % (path, ', '.join(allowed_extensions)))


if __name__ == '__main__':
    main()
