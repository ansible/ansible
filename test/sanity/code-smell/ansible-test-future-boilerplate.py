from __future__ import annotations

import ast
import sys


def main():
    # The following directories contain code which must work under Python 2.x.
    py2_compat = (
        'test/lib/ansible_test/_util/target/',
    )

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if any(path.startswith(prefix) for prefix in py2_compat):
            continue

        with open(path, 'rb') as path_fd:
            lines = path_fd.read().splitlines()

        missing = True
        if not lines:
            # Files are allowed to be empty of everything including boilerplate
            missing = False

        invalid_future = []

        for text in lines:
            if text == b'from __future__ import annotations':
                missing = False
                break

            if text.startswith(b'from __future__ ') or text == b'__metaclass__ = type':
                invalid_future.append(text.decode())

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
            print('%s: missing: from __future__ import annotations' % path)

        for text in invalid_future:
            print('%s: invalid: %s' % (path, text))


if __name__ == '__main__':
    main()
