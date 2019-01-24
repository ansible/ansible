#!/usr/bin/env python

import sys


def main():
    skip = set([
        'lib/ansible/compat/selectors/_selectors2.py',
        'lib/ansible/module_utils/six/_six.py',
        'setup.py',
    ])

    prune = [
        'contrib/inventory/',
        'contrib/vault/',
        'docs/',
        'examples/',
        'hacking/',
        'lib/ansible/module_utils/',
        'lib/ansible/modules/cloud/amazon/',
        'lib/ansible/modules/cloud/cloudstack/',
        'lib/ansible/modules/cloud/ovirt/',
        'lib/ansible/modules/network/aos/',
        'lib/ansible/modules/network/avi/',
        'lib/ansible/modules/network/cloudengine/',
        'lib/ansible/modules/network/eos/',
        'lib/ansible/modules/network/ios/',
        'lib/ansible/modules/network/netvisor/',
        'lib/ansible/modules/network/nxos/',
        'lib/ansible/modules/network/panos/',
        'lib/ansible/modules/network/vyos/',
        'lib/ansible/modules/windows/',
        'lib/ansible/plugins/doc_fragments/',
        'test/'
    ]

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        if any(path.startswith(p) for p in prune):
            continue

        with open(path, 'r') as path_fd:
            future_ok = None
            metaclass_ok = None

            lines = path_fd.read().splitlines()

            if not lines:
                continue

            for line, text in enumerate(lines):
                if text in ('from __future__ import (absolute_import, division, print_function)',
                            'from __future__ import absolute_import, division, print_function'):
                    future_ok = line

                if text == '__metaclass__ = type':
                    metaclass_ok = line

                if future_ok and metaclass_ok:
                    break

            if future_ok is None:
                print('%s: missing: from __future__ import (absolute_import, division, print_function)' % path)

            if metaclass_ok is None:
                print('%s: missing: __metaclass__ = type' % path)


if __name__ == '__main__':
    main()
