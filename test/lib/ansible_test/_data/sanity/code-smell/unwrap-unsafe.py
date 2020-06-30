#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys

UNWRAP_RE = re.compile(r'^.*\bunwrap_var\(')

# Format is the file as the key, and the number of appearances to ignore
# All changes to the whitelist need to be approved by an Ansible core committer
WHITELIST = {
    'lib/ansible/utils/unsafe_proxy.py': 4,
    'lib/ansible/plugins/filter/core.py': 2,
}


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        found = 0
        with open(path, 'r') as f:
            for line in f.readlines():
                matches = UNWRAP_RE.findall(line)
                if matches:
                    found += 1

        if found > WHITELIST.get(path, 0):
            print(
                '%s: use of unwrap_var is strictly monitored for incorrect use. Please seek guidance from a core committer' % (path,)
            )


if __name__ == '__main__':
    main()
