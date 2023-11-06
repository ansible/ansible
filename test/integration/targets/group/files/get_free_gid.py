
from __future__ import annotations

import grp


def main():
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
