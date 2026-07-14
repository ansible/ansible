# auto-shebang
"""Provides an entry point for python scripts and python modules on the controller with the current python interpreter and optional code coverage collection."""
from __future__ import annotations

import importlib.util
import os
import sys

NETWORKING_CLI_STUB_SCRIPT = 'ansible_connection_cli_stub.py'


def main():
    """Main entry point."""
    name = os.path.basename(__file__)
    args = [sys.executable]

    ansible_lib_root = os.environ.get('ANSIBLE_TEST_ANSIBLE_LIB_ROOT')
    debugger_config = os.environ.get('ANSIBLE_TEST_DEBUGGER_CONFIG')
    coverage_config = os.environ.get('COVERAGE_CONF')
    coverage_output = os.environ.get('COVERAGE_FILE')

    if coverage_config:
        if coverage_output:
            args += ['-m', 'coverage.__main__', 'run', '--rcfile', coverage_config]
        else:
            found = bool(importlib.util.find_spec('coverage'))

            if not found:
                sys.exit('ERROR: Could not find `coverage` module. '
                         'Did you use a virtualenv created without --system-site-packages or with the wrong interpreter?')

    if debugger_config:
        import json

        debugger_options = json.loads(debugger_config)
        os.environ.update(debugger_options['env'])
        args += debugger_options['args']

    if name == 'python.py':
        if sys.argv[1] == '-c':
            # prevent simple misuse of python.py with -c which does not work with coverage
            sys.exit('ERROR: Use `python -c` instead of `python.py -c` to avoid errors when code coverage is collected.')
    elif name == 'pytest':
        args += ['-m', 'pytest']
    elif name == 'importer.py':
        args += [find_program(name, False)]
    elif name == NETWORKING_CLI_STUB_SCRIPT:
        args += [os.path.join(ansible_lib_root, 'cli/scripts', NETWORKING_CLI_STUB_SCRIPT)]
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
    seen = {os.path.abspath(__file__)}
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
