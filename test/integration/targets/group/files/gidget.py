#!/usr/bin/env python

import grp

gids = [g.gr_gid for g in grp.getgrall()]

i = 0
while True:
    if i not in gids:
        print(i)
        break
    i += 1
