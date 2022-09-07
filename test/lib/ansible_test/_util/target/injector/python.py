# auto-shebang
"""Provides an entry point for python scripts and python modules on the controller with the current python interpreter and optional code coverage collection."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def main():
    """Main entry point."""
    name = os.path.basename(__file__)
    args = [sys.executable]

    coverage_config = os.environ.get('COVERAGE_CONF')
    coverage_output = os.environ.get('COVERAGE_FILE')

    if coverage_config:
        if coverage_output:
            args += ['-m', 'coverage.__main__', 'run', '--rcfile', coverage_config]
        else:
            if sys.version_info >= (3, 4):
                # noinspection PyUnresolvedReferences
                import importlib.util

                # noinspection PyUnresolvedReferences
                found = bool(importlib.util.find_spec('coverage'))
            else:
                # noinspection PyDeprecation
                import imp

                try:
                    # noinspection PyDeprecation
                    imp.find_module('coverage')
                    found = True
                except ImportError:
                    found = False

            if not found:
                sys.exit('ERROR: Could not find `coverage` module. '
                         'Did you use a virtualenv created without --system-site-packages or with the wrong interpreter?')

    if name == 'python.py':
        if sys.argv[1] == '-c':
            # prevent simple misuse of python.py with -c which does not work with coverage
            sys.exit('ERROR: Use `python -c` instead of `python.py -c` to avoid errors when code coverage is collected.')
    elif name == 'pytest':
        args += ['-m', 'pytest']
    elif name == 'importer.py':
        args += [find_program(name, False)]
    else:
        args += [find_program(name, True)]

    args += sys.argv[1:]

    os.execv(args[0], args)


def find_program(name, executable):  # type: (str, bool) -> str
    """
    Find and return the full path to the named program, optionally requiring it to be executable.
    Raises an exception if the program is not found.
    """
    path = os.environ.get('PATH', os.path.defpath)
    seen = set([os.path.abspath(__file__)])
    mode = os.F_OK | os.X_OK if executable else os.F_OK

    for base in path.split(os.path.pathsep):
        candidate = os.path.abspath(os.path.join(base, name))

        if candidate in seen:
            continue

        seen.add(candidate)

        if os.path.exists(candidate) and os.access(candidate, mode):
            return candidate

    raise Exception('Executable "%s" not found in path: %s' % (name, path))


if __name__ == '__main__':
    main()
