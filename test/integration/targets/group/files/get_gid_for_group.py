
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import grp
import os
import sys

GROUPFILE = "/etc/group"


def main():
    group_name = None
    if len(sys.argv) >= 2:
        group_name = sys.argv[1]

    prefix_path = None
    if len(sys.argv) >= 3:
        prefix_path = sys.argv[2]

    if prefix_path is not None:
        group_file = os.path.normpath(prefix_path + GROUPFILE)
        with open(group_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('{0}:'.format(group_name)):
                    entries = line.split(':')
                    print(entries[2])  # Print the gid
                    break
    else:
        print(grp.getgrnam(group_name).gr_gid)


if __name__ == '__main__':
    main()
