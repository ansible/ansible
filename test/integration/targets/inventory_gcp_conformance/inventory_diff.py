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
    # hosts in gce.py vs gcp_compose.py aren't the same
    ahosts = sorted(adata['_meta']['hostvars'].keys())
    bhosts = sorted(bdata['_meta']['hostvars'].keys())
    for ahost in ahosts:
        print('assert host %s exists in both inventories' % ahost)
        assert ahost in bhosts

    # all groups should be present obviously
    agroups = list(adata.keys())
    agroups.remove('_meta')
    if 'all' in agroups:
        agroups.remove('all')
    agroups = sorted(agroups)
    bgroups = list(bdata.keys())
    bgroups.remove('_meta')
    if 'all' in bgroups:
        bgroups.remove('all')
    bgroups = sorted(bgroups)

    for agroup in agroups:
        print('assert %s group is in both inventories' % agroup)
        assert agroup in bgroups

    for ahost in ahosts:
        ahost_vars = adata['_meta']['hostvars'][ahost]
        for k, v in ahost_vars.items():

            if k.startswith('gce_') and k != 'gce_uuid':
                print('assert var', k, v, k in bdata['_meta']['hostvars'][ahost], bdata['_meta']['hostvars'][ahost].get(k))
                assert k in bdata['_meta']['hostvars'][ahost], "%s not in b's %s hostvars" % (k, ahost)
                assert v == bdata['_meta']['hostvars'][ahost][k], "%s != %s" % (v, bdata['_meta']['hostvars'][ahost][k])


if __name__ == "__main__":
    main()
