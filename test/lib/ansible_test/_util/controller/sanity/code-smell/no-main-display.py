from __future__ import annotations

import sys

MAIN_DISPLAY_IMPORT = 'from __main__ import display'


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r') as file:
            for i, line in enumerate(file.readlines()):
                if MAIN_DISPLAY_IMPORT in line:
                    lineno = i + 1
                    colno = line.index(MAIN_DISPLAY_IMPORT) + 1
                    print('%s:%d:%d: Display is a singleton, just import and instantiate' % (path, lineno, colno))


if __name__ == '__main__':
    main()
