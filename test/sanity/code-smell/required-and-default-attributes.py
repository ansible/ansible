from __future__ import annotations

import re
import sys


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'(FieldAttribute.*(default|required).*(default|required))', text)

                if match:
                    print('%s:%d:%d: use only one of `default` or `required` with `FieldAttribute`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
