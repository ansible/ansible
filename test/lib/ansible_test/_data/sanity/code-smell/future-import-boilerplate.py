#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            lines = path_fd.read().splitlines()

        missing = True
        if not lines:
            # Files are allowed to be empty of everything including boilerplate
            missing = False

        for text in lines:
            if text in (b'from __future__ import (absolute_import, division, print_function)',
                        b'from __future__ import absolute_import, division, print_function'):
                missing = False
                break

        if missing:
            with open(path) as file:
                contents = file.read()

            # noinspection PyBroadException
            try:
                node = ast.parse(contents)

                # files consisting of only assignments have no need for future import boilerplate
                # the only exception would be division during assignment, but we'll overlook that for simplicity
                # the most likely case is that of a documentation only python file
                if all(isinstance(statement, ast.Assign) for statement in node.body):
                    missing = False
            except Exception:  # pylint: disable=broad-except
                pass  # the compile sanity test will report this error

        if missing:
            print('%s: missing: from __future__ import (absolute_import, division, print_function)' % path)


if __name__ == '__main__':
    main()
