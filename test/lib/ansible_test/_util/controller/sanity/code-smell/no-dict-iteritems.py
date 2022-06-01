"""Disallow use of the dict.iteritems function."""
from __future__ import annotations

import re
import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'r', encoding='utf-8') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'(?<! six)\.(iteritems)', text)

                if match:
                    print('%s:%d:%d: use `dict.items` or `ansible.module_utils.six.iteritems` instead of `dict.iteritems`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
