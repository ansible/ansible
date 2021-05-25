#!/usr/bin/env python
"""Sanity test using rstcheck and sphinx."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import subprocess
import sys


def main():
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    encoding = 'utf-8'

    ignore_substitutions = (
        'br',
    )

    cmd = [
        sys.executable,
        '-m', 'rstcheck',
        '--report', 'warning',
        '--ignore-substitutions', ','.join(ignore_substitutions),
    ] + paths

    process = subprocess.run(cmd,
                             stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             check=False,
                             )

    if process.stdout:
        raise Exception(process.stdout)

    pattern = re.compile(r'^(?P<path>[^:]*):(?P<line>[0-9]+): \((?P<level>INFO|WARNING|ERROR|SEVERE)/[0-4]\) (?P<message>.*)$')

    results = parse_to_list_of_dict(pattern, process.stderr.decode(encoding))

    for result in results:
        print('%s:%s:%s: %s' % (result['path'], result['line'], 0, result['message']))


def parse_to_list_of_dict(pattern, value):
    matched = []
    unmatched = []

    for line in value.splitlines():
        match = re.search(pattern, line)

        if match:
            matched.append(match.groupdict())
        else:
            unmatched.append(line)

    if unmatched:
        raise Exception('Pattern "%s" did not match values:\n%s' % (pattern, '\n'.join(unmatched)))

    return matched


if __name__ == '__main__':
    main()
