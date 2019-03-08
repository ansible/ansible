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
        print('assert %s group is in b' % agroup)

        # FIXME
        # THIS STILL NEEDS AN ADAPTER BEFORE IT WILL WORK
        # i-100 vs. i_100
        if '-' in agroup:
            continue

        assert agroup in bgroups

    for ahost in ahosts:
        ahost_vars = adata['_meta']['hostvars'][ahost]
        for k, v in ahost_vars.items():

            # tags are a dict in the plugin
            if k.startswith('ec2_tag'):
                print('assert tag', k, v)
                assert 'tags' in bdata['_meta']['hostvars'][ahost], 'b file does not have tags in host'
                btags = bdata['_meta']['hostvars'][ahost]['tags']
                tagkey = k.replace('ec2_tag_', '')
                assert tagkey in btags, '%s tag not in b file host tags' % tagkey
                assert v == btags[tagkey], '%s != %s' % (v, btags[tagkey])
                continue

            print('assert var', k, v, k in bdata['_meta']['hostvars'][ahost], bdata['_meta']['hostvars'][ahost].get(k))
            assert k in bdata['_meta']['hostvars'][ahost], "%s not in b's %s hostvars" % (k, ahost)
            assert v == bdata['_meta']['hostvars'][ahost][k], "%s != %s" % (v, bdata['_meta']['hostvars'][ahost][k])


if __name__ == "__main__":
    main()
