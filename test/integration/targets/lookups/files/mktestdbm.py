#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)

import sys
try:
    import dbm as db
except ImportError:
    import dbm.ndbm as db


def main():
    d = db.open(sys.argv[1], 'n')
    d['k1'] = 'v1'
    d['k2'] = 'v2'
    d.close()

if __name__ == "__main__":
    main()
