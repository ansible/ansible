#!/usr/bin/env python
from __future__ import print_function

import os
import re
import sys

from collections import defaultdict

PATH = 'lib/ansible'
ASSERT_RE = re.compile(r'.*(?<![-:a-zA-Z#][ -])\bassert\b(?!:).*')

all_matches = defaultdict(list)

for dirpath, dirnames, filenames in os.walk(PATH):
    for filename in filenames:
        path = os.path.join(dirpath, filename)
        if not os.path.isfile(path) or not path.endswith('.py'):
            continue

        with open(path, 'r') as f:
            for i, line in enumerate(f.readlines()):
                matches = ASSERT_RE.findall(line)

                if matches:
                    all_matches[path].append((i + 1, line.index('assert') + 1, matches))


if all_matches:
    print('Use of assert in production code is not recommended.')
    print('Python will remove all assert statements if run with optimizations')
    print('Alternatives:')
    print('    if not isinstance(value, dict):')
    print('        raise AssertionError("Expected a dict for value")')

    for path, matches in all_matches.items():
        for line_matches in matches:
            for match in line_matches[2]:
                print('%s:%d:%d: %s' % ((path,) + line_matches[:2] + (match,)))
    sys.exit(1)
