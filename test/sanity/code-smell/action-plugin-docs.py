#!/usr/bin/env python
"""Test to verify action plugins have an associated module to provide documentation."""

import os


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

    module_names = set()

    for root, dirs, files in os.walk('lib/ansible/modules'):
        for filename in files:
            name, ext = os.path.splitext(filename)

            if ext == '.py' and name != '__init__':
                if name.startswith('_'):
                    name = name[1:]

                module_names.add(name)

    action_plugin_dir = 'lib/ansible/plugins/action'
    unused_skip = set(skip)

    for filename in os.listdir(action_plugin_dir):
        name, ext = os.path.splitext(filename)

        if ext == '.py' and name not in module_names:
            if name in skip:
                unused_skip.remove(name)
                continue

            path = os.path.join(action_plugin_dir, filename)

            print('%s: action plugin has no matching module to provide documentation' % path)

    for filename in sorted(unused_skip):
        print("%s: remove '%s' from skip list since it does not exist" % ('test/sanity/code-smell/action-plugin-docs.py', filename))


if __name__ == '__main__':
    main()
