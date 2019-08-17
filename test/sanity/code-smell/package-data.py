#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import os
import re
import sys
import tempfile
import subprocess


def assemble_files_to_look_for():
    """
    This looks for all of the files which should show up in an installation of ansible
    """
    ignore_files = frozenset((
        '*/ansible/galaxy/data/default/*/.git_keep',
        '*/ansible/galaxy/data/default/role/*/main.yml.j2',
        '*/ansible/galaxy/data/default/role/*/test.yml.j2',
        '*/ansible/galaxy/data/default/collection/plugins/README.md.j2',
        '*/ansible_test/tests/*',
        '*/ansible_test/tests/*/*',
    ))

    pkg_data_files = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path.startswith("lib/ansible"):
            if os.path.splitext(path)[1] != '.py':
                for ignore in ignore_files:
                    if fnmatch.fnmatch(path, ignore):
                        break
                else:
                    pkg_data_files.append(os.path.relpath(path, 'lib'))

        elif path.startswith("test/lib/ansible_test"):
            for ignore in ignore_files:
                if fnmatch.fnmatch(path, ignore):
                    break
            else:
                pkg_data_files.append(os.path.relpath(path, 'test/lib'))

    return pkg_data_files


def main():
    pkg_data_files = assemble_files_to_look_for()

    with tempfile.TemporaryDirectory() as tmp_dir:
        stdout, _dummy = subprocess.Popen(
            ['python', 'setup.py', 'install', '--root=%s' % tmp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ).communicate()
        match = re.search('^creating (%s/.*?/(?:site|dist)-packages)/ansible$' %
                          tmp_dir, stdout, flags=re.M)

        for filename in pkg_data_files:
            path = os.path.join(match.group(1), filename)
            if not os.path.exists(path):
                print('%s: File not installed' % os.path.join('lib', filename))


if __name__ == '__main__':
    main()
