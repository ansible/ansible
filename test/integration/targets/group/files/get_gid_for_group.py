
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import grp
import sys


def main():
    group_name = None
    if len(sys.argv) >= 2:
        group_name = sys.argv[1]

    print(grp.getgrnam(group_name).gr_gid)


if __name__ == '__main__':
    main()
