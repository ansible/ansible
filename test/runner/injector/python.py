#!/usr/bin/env python
"""Provides an entry point for python scripts and python modules on the controller with the current python interpreter and optional code coverage collection."""

import os
import sys


def main():
    """Main entry point."""
    name = os.path.basename(__file__)
    args = [sys.executable]

    coverage_config = os.environ.get('_ANSIBLE_COVERAGE_CONFIG')

    if coverage_config:
        args += ['-m', 'coverage.__main__', 'run', '--rcfile', coverage_config]

    if name == 'python.py':
        if sys.argv[1] == '-c':
            # prevent simple misuse of python.py with -c which does not work with coverage
            sys.exit('ERROR: Use `python -c` instead of `python.py -c` to avoid errors when code coverage is collected.')
    elif name == 'pytest':
        args += ['-m', 'pytest']
    else:
        args += [find_executable(name)]

    args += sys.argv[1:]

    os.execv(args[0], args)


def find_executable(name):
    """
    :type name: str
    :rtype: str
    """
    path = os.environ.get('PATH', os.path.defpath)
    seen = set([os.path.abspath(__file__)])

    for base in path.split(os.path.pathsep):
        candidate = os.path.abspath(os.path.join(base, name))

        if candidate in seen:
            continue

        seen.add(candidate)

        if os.path.exists(candidate) and os.access(candidate, os.F_OK | os.X_OK):
            return candidate

    raise Exception('Executable "%s" not found in path: %s' % (name, path))


if __name__ == '__main__':
    main()
