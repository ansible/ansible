"""Require files to end in \n"""

from __future__ import annotations

import sys
import os

def main():
    """Main entry point."""
    fix_mode = bool(int(os.environ['ANSIBLE_TEST_FIX_MODE']))
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'ab+') as path_fd:
            try:
                path_fd.seek(-1, 2)  # End of the file minus one byte
            except OSError as e:  # catch empty files
                continue
            last_char = path_fd.read(1)
            if last_char != b'\n':
                if fix_mode:
                    path_fd.write(b'\n')
                else:
                    print(f'{path}: text files should end with a newline character "\\n"')


if __name__ == '__main__':
    main()
