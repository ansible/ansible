#!/usr/bin/env python

import os


def main():
    skip_dirs = set([
        '.tox',
    ])

    for root, dirs, files in os.walk('.'):
        for skip_dir in skip_dirs:
            if skip_dir in dirs:
                dirs.remove(skip_dir)

        if root == '.':
            root = ''
        elif root.startswith('./'):
            root = root[2:]

        for file in files:
            path = os.path.join(root, file)

            if not os.path.exists(path):
                print('%s: broken symlinks are not allowed' % path)

        for directory in dirs:
            path = os.path.join(root, directory)

            if os.path.islink(path):
                print('%s: symlinks to directories are not allowed' % path)


if __name__ == '__main__':
    main()
