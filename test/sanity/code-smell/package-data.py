#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile
import subprocess

Text = type(u'')


def to_bytes(value, errors='strict'):
    """Return the given value as bytes encoded using UTF-8 if not already bytes."""
    if isinstance(value, bytes):
        return value

    if isinstance(value, Text):
        return value.encode('utf-8', errors)

    raise Exception('value is not bytes or text: %s' % type(value))


def main():
    devnull = open(os.devnull, 'w')

    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    subprocess.check_call(['python', 'setup.py', 'sdist', '--manifest-only'], stdout=devnull, stderr=devnull)

    package_roots = [
        (b'lib/ansible', len(b'lib/')),
        (b'test/lib/ansible_test', len(b'test/lib/'))
    ]

    with open('MANIFEST', 'rb') as fd:
        manifest_files = set()
        for f in fd.readlines():
            # we only care about the files in the package roots- strip everything before the package name
            manifest_files.update((f[p[1]:].strip() for p in package_roots if f.startswith(p[0])))

    with tempfile.TemporaryDirectory() as tmp_dir:
        subprocess.check_call(['python', 'setup.py', 'install', '--no-compile', '--prefix=', '--root={0}'
                              .format(tmp_dir)], stdout=devnull, stderr=devnull)

        installed_files = set()

        install_root = None

        for root, dirs, files in os.walk(tmp_dir):
            if not install_root:
                # FIXME: use package_roots tuples
                # find the install root so we can strip it off to compare with the manifest
                if 'ansible' in dirs and 'ansible_test' in dirs:
                    install_root = root
                else:
                    continue

            curdir = os.path.relpath(root, install_root)  # chop off the install root

            installed_files.update((to_bytes(os.path.join(curdir, p)) for p in files))

    missing_files = manifest_files.difference(installed_files)

    for f in missing_files:
        print('{0}: file not installed'.format(f))


if __name__ == '__main__':
    main()
