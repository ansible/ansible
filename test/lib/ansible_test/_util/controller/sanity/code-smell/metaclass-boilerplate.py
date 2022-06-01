"""Require __metaclass__ boilerplate for code that supports Python 2.x."""
from __future__ import annotations

import ast
import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            lines = path_fd.read().splitlines()

        missing = True
        if not lines:
            # Files are allowed to be empty of everything including boilerplate
            missing = False

        for text in lines:
            if text == b'__metaclass__ = type':
                missing = False
                break

        if missing:
            with open(path, encoding='utf-8') as file:
                contents = file.read()

            # noinspection PyBroadException
            try:
                node = ast.parse(contents)

                # files consisting of only assignments have no need for metaclass boilerplate
                # the most likely case is that of a documentation only python file
                if all(isinstance(statement, ast.Assign) for statement in node.body):
                    missing = False
            except Exception:  # pylint: disable=broad-except
                pass  # the compile sanity test will report this error

        if missing:
            print('%s: missing: __metaclass__ = type' % path)


if __name__ == '__main__':
    main()
