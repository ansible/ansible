#!/usr/bin/env python

import os


def main():
    # required by external automated processes and should not be moved, renamed or converted to a symbolic link
    path = 'examples/scripts/ConfigureRemotingForAnsible.ps1'
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
