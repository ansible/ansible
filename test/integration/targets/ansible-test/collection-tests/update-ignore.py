#!/usr/bin/env python
"""Rewrite a sanity ignore file to expand Python versions for import ignores and write the file out with the correct Ansible version in the name."""

import os
import sys

from ansible import release


def main():
    ansible_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(release.__file__))))
    source_root = os.path.join(ansible_root, 'test', 'lib')

    sys.path.insert(0, source_root)

    from ansible_test._internal import constants

    src_path = 'tests/sanity/ignore.txt'
    directory = os.path.dirname(src_path)
    name, ext = os.path.splitext(os.path.basename(src_path))
    major_minor = '.'.join(release.__version__.split('.')[:2])
    dst_path = os.path.join(directory, f'{name}-{major_minor}{ext}')

    with open(src_path) as src_file:
        src_lines = src_file.read().splitlines()

    dst_lines = []

    for line in src_lines:
        path, rule = line.split(' ')

        if rule != 'import':
            dst_lines.append(line)
            continue

        if path.startswith('plugins/module'):
            python_versions = constants.SUPPORTED_PYTHON_VERSIONS
        else:
            python_versions = constants.CONTROLLER_PYTHON_VERSIONS

        for python_version in python_versions:
            dst_lines.append(f'{line}-{python_version}')

    ignores = '\n'.join(dst_lines) + '\n'

    with open(dst_path, 'w') as dst_file:
        dst_file.write(ignores)


if __name__ == '__main__':
    main()
