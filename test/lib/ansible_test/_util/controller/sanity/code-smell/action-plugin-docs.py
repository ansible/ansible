"""Test to verify action plugins have an associated module to provide documentation."""

from __future__ import annotations

import os
import sys


def main():
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    module_names = set()

    module_prefixes = {
        'lib/ansible/modules/': True,
        'plugins/modules/': False,
    }

    action_prefixes = {
        'lib/ansible/plugins/action/': True,
        'plugins/action/': False,
    }

    for path in paths:
        full_name = get_full_name(path, module_prefixes)

        if full_name:
            module_names.add(full_name)

    for path in paths:
        full_name = get_full_name(path, action_prefixes, extensions=('.py',))

        if full_name and full_name not in module_names:
            print('%s: action plugin has no matching module to provide documentation' % path)


def get_full_name(path: str, prefixes: dict[str, bool], extensions: tuple[str] | None = None) -> str | None:
    """Return the full name of the plugin at the given path by matching against the given path prefixes, or None if no match is found."""
    for prefix, flat in prefixes.items():
        if path.startswith(prefix):
            relative_path = os.path.relpath(path, prefix)

            if flat:
                full_name = os.path.basename(relative_path)
            else:
                full_name = relative_path

            full_name, file_ext = os.path.splitext(full_name)

            name = os.path.basename(full_name)

            if name == '__init__':
                return None

            if extensions and file_ext not in extensions:
                return None

            if name.startswith('_'):
                name = name[1:]

            full_name = os.path.join(os.path.dirname(full_name), name).replace(os.path.sep, '.')

            return full_name

    return None


if __name__ == '__main__':
    main()
