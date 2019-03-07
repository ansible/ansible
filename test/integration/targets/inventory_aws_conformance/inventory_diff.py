#!/usr/bin/env python

import json
import os
import sys


def main():
    # a should be the source of truth (the script output)
    a = sys.argv[1]
    # b should be the thing to check (the plugin output)
    b = sys.argv[2]

    with open(a, 'r') as f:
        adata = json.loads(f.read())
    with open(b, 'r') as f:
        bdata = json.loads(f.read())

    # all hosts should be present obviously
    ahosts = sorted(adata['_meta']['hostvars'].keys())
    bhosts = sorted(bdata['_meta']['hostvars'].keys())
    assert ahosts == bhosts

    # all groups should be present obviously
    agroups = adata.keys()
    agroups.remove('_meta')
    if 'all' in agroups:
        agroups.remove('all')
    agroups = sorted(agroups)
    bgroups = bdata.keys()
    bgroups.remove('_meta')
    if 'all' in bgroups:
        bgroups.remove('all')
    bgroups = sorted(bgroups)

    for agroup in agroups:
        print(agroup)
        #import epdb; epdb.st()

        # i-100 vs. i_100
        if '-' in agroup:
            continue
        assert agroup in bgroups

    import epdb; epdb.st()



if __name__ == "__main__":
    main()
