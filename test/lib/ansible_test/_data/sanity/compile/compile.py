#!/usr/bin/env python
"""Python syntax checker with lint friendly output."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import warnings

with warnings.catch_warnings():
    # The parser module is deprecated as of Python 3.9.
    # This implementation will need to be updated to use another solution.
    # Until then, disable the deprecation warnings to prevent test failures.
    warnings.simplefilter('ignore', DeprecationWarning)
    import parser

import sys


def main():
    status = 0

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as source_fd:
            if sys.version_info[0] == 3:
                source = source_fd.read().decode('utf-8')
            else:
                source = source_fd.read()

        try:
            parser.suite(source)
        except SyntaxError:
            ex = sys.exc_info()[1]
            status = 1
            message = ex.text.splitlines()[0].strip()
            sys.stdout.write("%s:%d:%d: SyntaxError: %s\n" % (path, ex.lineno, ex.offset, message))
            sys.stdout.flush()

    sys.exit(status)


if __name__ == '__main__':
    main()
