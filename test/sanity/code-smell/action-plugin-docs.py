#!/usr/bin/env python
"""Test to verify action plugins have an associated module to provide documentation."""

import os
import sys


def main():
    """Main entry point."""
    skip = set([
        '__init__',  # action plugin base class, not an actual action plugin
        'net_base',  # base class for other net_* action plugins which have a matching module
        'normal',  # default action plugin for modules without a dedicated action plugin
        'network',  # base class for network action plugins

        # The following action plugins existed without modules to document them before this test was put in place.
        # They should either be removed, have a module added to document them, or have the exception documented here.
        'bigip',
        'bigiq',
        'ce_template',

        # The following action plugins provide base classes for network platform specific modules to support `connection: local`.
        # Once we fully deprecate the use of connection local, the base classes will go away.
        'aireos',
        'aruba',
        'asa',
        'ce',
        'cnos',
        'dellos10',
        'dellos6',
        'dellos9',
        'enos',
        'eos',
        'ios',
        'iosxr',
        'ironware',
        'junos',
        'netconf',
        'nxos',
        'sros',
        'vyos',
    ])

    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    module_names = set()

    for path in paths:
        if not path.startswith('lib/ansible/modules/'):
            continue

        name = os.path.splitext(os.path.basename(path))[0]

        if name != '__init__':
            if name.startswith('_'):
                name = name[1:]

            module_names.add(name)

    unused_skip = set(skip)

    for path in paths:
        if not path.startswith('lib/ansible/plugins/action/'):
            continue

        name = os.path.splitext(os.path.basename(path))[0]

        if name not in module_names:
            if name in skip:
                unused_skip.remove(name)
                continue

            print('%s: action plugin has no matching module to provide documentation' % path)

    for filename in sorted(unused_skip):
        print("%s: remove '%s' from skip list since it does not exist" % ('test/sanity/code-smell/action-plugin-docs.py', filename))


if __name__ == '__main__':
    main()
