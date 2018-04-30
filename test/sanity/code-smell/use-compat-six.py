#!/usr/bin/env python

import os
import re
import sys


def main():
    skip = set([
        'test/sanity/code-smell/%s' % os.path.basename(__file__),
        # digital_ocean is checking for six because dopy doesn't specify the
        # requirement on six so it needs to try importing six to give the correct error message
        'lib/ansible/modules/cloud/digital_ocean/digital_ocean.py',
        # correct imports in the following files and remove them from this list
        'contrib/inventory/apache-libcloud.py',
        'contrib/inventory/cobbler.py',
        'contrib/inventory/collins.py',
        'contrib/inventory/consul_io.py',
        'contrib/inventory/ec2.py',
        'contrib/inventory/freeipa.py',
        'contrib/inventory/lxd.py',
        'contrib/inventory/nova.py',
        'contrib/inventory/nsot.py',
        'contrib/inventory/packet_net.py',
        'contrib/inventory/proxmox.py',
        'contrib/inventory/rax.py',
        'contrib/inventory/rudder.py',
        'contrib/inventory/scaleway.py',
        'contrib/inventory/spacewalk.py',
        'contrib/inventory/vmware.py',
        'contrib/inventory/vmware_inventory.py',
        'docs/bin/plugin_formatter.py',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        if path.startswith('test/sanity/pylint/plugins/'):
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'((^\s*import\s+six\b)|(^\s*from\s+six\b))', text)

                if match:
                    print('%s:%d:%d: use `ansible.module_utils.six` instead of `six`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
