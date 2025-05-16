"""Prevent unwanted files from being added to the source tree."""

from __future__ import annotations

import os
import sys


def main():
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    allowed_extensions = {
        '.cs',
        '.ps1',
        '.psm1',
        '.py',
    }

    skip_paths = {
        'lib/ansible/config/ansible_builtin_runtime.yml',  # not included in the sanity ignore file since it won't exist until after migration
    }

    skip_directories = {
        'lib/ansible/galaxy/data/',
    }

    allow_yaml = {
        'lib/ansible/plugins/test',
        'lib/ansible/plugins/filter',
        'lib/ansible/_internal/ansible_collections',
    }

    for path in paths:
        if path in skip_paths:
            continue

        if any(path.startswith(skip_directory) for skip_directory in skip_directories):
            continue

        if path.startswith('lib/') and not path.startswith('lib/ansible/'):
            print('%s: all "lib" content must reside in the "lib/ansible" directory' % path)
            continue

        ext = os.path.splitext(path)[1]
        if ext in ('.yml',) and any(path.startswith(yaml_directory) for yaml_directory in allow_yaml):
            continue

        if ext not in allowed_extensions:
            print('%s: extension must be one of: %s' % (path, ', '.join(allowed_extensions)))


if __name__ == '__main__':
    main()
