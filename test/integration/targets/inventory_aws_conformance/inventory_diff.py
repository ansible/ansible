#!/usr/bin/env python

import json
import sys


def check_hosts(contrib, plugin):
    contrib_hosts = sorted(contrib['_meta']['hostvars'].keys())
    plugin_hosts = sorted(plugin['_meta']['hostvars'].keys())
    assert contrib_hosts == plugin_hosts
    return contrib_hosts, plugin_hosts


def check_groups(contrib, plugin):
    contrib_groups = set(contrib.keys())
    plugin_groups = set(plugin.keys())
    missing_groups = contrib_groups.difference(plugin_groups)
    if missing_groups:
        print("groups: %s are missing from the plugin" % missing_groups)
    assert not missing_groups
    return contrib_groups, plugin_groups


def check_host_vars(key, value, plugin, host):
    # tags are a dict in the plugin
    if key.startswith('ec2_tag'):
        print('assert tag', key, value)
        assert 'tags' in plugin['_meta']['hostvars'][host], 'b file does not have tags in host'
        btags = plugin['_meta']['hostvars'][host]['tags']
        tagkey = key.replace('ec2_tag_', '')
        assert tagkey in btags, '%s tag not in b file host tags' % tagkey
        assert value == btags[tagkey], '%s != %s' % (value, btags[tagkey])
    else:
        print('assert var', key, value, key in plugin['_meta']['hostvars'][host], plugin['_meta']['hostvars'][host].get(key))
        assert key in plugin['_meta']['hostvars'][host], "%s not in b's %s hostvars" % (key, host)
        assert value == plugin['_meta']['hostvars'][host][key], "%s != %s" % (value, plugin['_meta']['hostvars'][host][key])


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
    ahosts, bhosts = check_hosts(adata, bdata)

    # all groups should be present obviously
    agroups, bgroups = check_groups(adata, bdata)

    # check host vars can be reconstructed
    for ahost in ahosts:
        contrib_host_vars = adata['_meta']['hostvars'][ahost]
        for key, value in contrib_host_vars.items():
            check_host_vars(key, value, bdata, ahost)


if __name__ == "__main__":
    main()
