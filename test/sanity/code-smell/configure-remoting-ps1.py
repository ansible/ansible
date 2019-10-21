#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os


def main():
    # required by external automated processes and should not be moved, renamed or converted to a symbolic link
    original = 'examples/scripts/ConfigureRemotingForAnsible.ps1'
    # required to be packaged with ansible-test and must match the original file, but cannot be a symbolic link
    # the packaged version is needed to run tests when ansible-test has been installed
    # keeping the packaged version identical to the original makes sure tests cover both files
    packaged = 'test/lib/ansible_test/_data/setup/ConfigureRemotingForAnsible.ps1'

    copy_valid = False

    if os.path.isfile(original) and os.path.isfile(packaged):
        with open(original, 'rb') as original_file:
            original_content = original_file.read()

        with open(packaged, 'rb') as packaged_file:
            packaged_content = packaged_file.read()

        if original_content == packaged_content:
            copy_valid = True

    if not copy_valid:
        print('%s: must be an exact copy of "%s"' % (packaged, original))

    for path in [original, packaged]:
        directory = path

        while True:
            directory = os.path.dirname(directory)

            if not directory:
                break

            if not os.path.isdir(directory):
                print('%s: must be a directory' % directory)

            if os.path.islink(directory):
                print('%s: cannot be a symbolic link' % directory)

        if not os.path.isfile(path):
            print('%s: must be a file' % path)

        if os.path.islink(path):
            print('%s: cannot be a symbolic link' % path)


if __name__ == '__main__':
    main()
