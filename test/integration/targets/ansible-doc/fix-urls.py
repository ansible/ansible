"""Unwrap URLs to docs.ansible.com and remove version"""
from __future__ import annotations

import re
import sys


def main():
    data = sys.stdin.read()
    data = re.sub('(https://docs\\.ansible\\.com/[^ ]+)\n +([^ ]+)\n', '\\1\\2\n', data, flags=re.MULTILINE)
    data = re.sub('https://docs\\.ansible\\.com/ansible(|-core)/(?:[^/]+)/', 'https://docs.ansible.com/ansible\\1/devel/', data)
    sys.stdout.write(data)


if __name__ == '__main__':
    main()
