
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import grp
import os
import sys

GROUPFILE = "/etc/group"


def main():
    prefix_path = None
    if len(sys.argv) >= 2:
        prefix_path = sys.argv[1]

    gids = []

    if prefix_path is not None:
        group_file = os.path.normpath(prefix_path + GROUPFILE)
        with open(group_file, 'rb') as f:
            lines = f.readlines()
            for line in lines:
                entries = line.split(b':')
                gids.append(int(entries[2]))  # 2 == group id
    else:
        gids = [g.gr_gid for g in grp.getgrall()]

    # Start the gid numbering with 1
    # FreeBSD doesn't support the usage of gid 0, it doesn't fail (rc=0) but instead a number in the normal
    # range is picked.
    i = 1
    while True:
        if i not in gids:
            print(i)
            break
        i += 1


if __name__ == '__main__':
    main()
