#!/usr/bin/env python
"""Python syntax checker with lint friendly output."""

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
            ex_type, ex, ex_traceback = sys.exc_info()
            status = 1
            message = ex.text.splitlines()[0].strip()
            sys.stdout.write("%s:%d:%d: SyntaxError: %s\n" % (path, ex.lineno, ex.offset, message))
            sys.stdout.flush()

    sys.exit(status)


if __name__ == '__main__':
    main()
