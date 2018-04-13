#!/usr/bin/env python

# a script to check for illegal filenames on various Operating Systems. The
# main rules are derived from restrictions on Windows
# https://msdn.microsoft.com/en-us/library/aa365247#naming_conventions

import os
import re
import struct

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


def check_path(path, dir=False):
    type_name = 'directory' if dir else 'file'
    parent, file_name = os.path.split(path)
    name, ext = os.path.splitext(file_name)

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
    pattern = re.compile("^test/integration/targets/.*/backup")

    for root, dirs, files in os.walk('.'):
        if root == '.':
            root = ''
        elif root.startswith('./'):
            root = root[2:]

        # ignore test/integration/targets/*/backup
        if pattern.match(root):
            continue

        for dir_name in dirs:
            check_path(os.path.join(root, dir_name), dir=True)

        for file_name in files:
            check_path(os.path.join(root, file_name), dir=False)


if __name__ == '__main__':
    main()
