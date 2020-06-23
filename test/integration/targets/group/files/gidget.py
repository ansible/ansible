#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import grp

gids = [g.gr_gid for g in grp.getgrall()]

i = 0
while True:
    if i not in gids:
        print(i)
        break
    i += 1
