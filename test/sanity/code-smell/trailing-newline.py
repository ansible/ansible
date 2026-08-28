"""Require files to end in \n"""

from __future__ import annotations

import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            try:
                path_fd.seek(-1, 2)  # End of the file minus one byte
            except OSError as e:  # catch empty files
                continue
            last_char = path_fd.read(1)
            if last_char != b'\n':
                print(f'{path}: text files should end with a newline character "\\n"')


if __name__ == '__main__':
    main()
