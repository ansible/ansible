#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import os
import re
import sys
import tempfile
import subprocess


def main():
    ignore_files = frozenset((
        '*/galaxy/data/default/*/.git_keep',
        '*/galaxy/data/default/role/*/main.yml.j2',
        '*/galaxy/data/default/role/*/test.yml.j2',
        '*/galaxy/data/default/collection/plugins/README.md.j2',
    ))

    non_py_files = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if os.path.splitext(path)[1] != '.py':
            add = True
            for ignore in ignore_files:
                if fnmatch.fnmatch(path, ignore):
                    add = False
            if add:
                non_py_files.append(os.path.relpath(path, 'lib/ansible'))

    with tempfile.TemporaryDirectory() as tmp_dir:
        stdout, _dummy = subprocess.Popen(
            ['python', 'setup.py', 'install', '--root=%s' % tmp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ).communicate()
        match = re.search('^creating (%s/.*?/(?:site|dist)-packages/ansible)$' % tmp_dir, stdout, flags=re.M)

        for filename in non_py_files:
            path = os.path.join(match.group(1), filename)
            if not os.path.exists(path):
                print('%s: File not installed' % os.path.join('lib', 'ansible', filename))


if __name__ == '__main__':
    main()
