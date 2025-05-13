from __future__ import annotations

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

        invalid_future = []

        for text in lines:
            if text in (
                b'from __future__ import annotations',
                b'from __future__ import annotations as _annotations',
                b'from __future__ import annotations  # pragma: nocover',
            ):
                missing = False
                break

            if text.strip().startswith(b'from __future__ ') or text.strip().startswith(b'__metaclass__ '):
                invalid_future.append(text.decode())

        if missing:
            with open(path) as file:
                contents = file.read()

            # noinspection PyBroadException
            try:
                node = ast.parse(contents)

                # files consisting of only assignments have no need for future import boilerplate
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
