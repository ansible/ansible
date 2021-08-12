#!/usr/bin/env python

# a script to check for illegal filenames on various Operating Systems. The
# main rules are derived from restrictions on Windows
# https://msdn.microsoft.com/en-us/library/aa365247#naming_conventions
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import struct
import sys

from ansible.module_utils.basic import to_bytes

ILLEGAL_CHARS = [
    b'<',
    b'>',
    b':',
    b'"',
    b'/',
    b'\\',
    b'|',
    b'?',
    b'*'
] + [struct.pack("b", i) for i in range(32)]

ILLEGAL_NAMES = [
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
]

ILLEGAL_END_CHARS = [
    '.',
    ' ',
]


def check_path(path, is_dir=False):
    type_name = 'directory' if is_dir else 'file'
    file_name = os.path.basename(path.rstrip(os.path.sep))
    name = os.path.splitext(file_name)[0]

    if name.upper() in ILLEGAL_NAMES:
        print("%s: illegal %s name %s" % (path, type_name, name.upper()))

    if file_name[-1] in ILLEGAL_END_CHARS:
        print("%s: illegal %s name end-char '%s'" % (path, type_name, file_name[-1]))

    bfile = to_bytes(file_name, encoding='utf-8')
    for char in ILLEGAL_CHARS:
        if char in bfile:
            bpath = to_bytes(path, encoding='utf-8')
            print("%s: illegal char '%s' in %s name" % (bpath, char, type_name))


def main():
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        check_path(path, is_dir=path.endswith(os.path.sep))


if __name__ == '__main__':
    main()
