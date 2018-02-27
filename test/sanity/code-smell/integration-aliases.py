#!/usr/bin/env python

import os
import textwrap


def main():
    targets_dir = 'test/integration/targets'

    with open('test/integration/target-prefixes.network', 'r') as prefixes_fd:
        network_prefixes = prefixes_fd.read().splitlines()

    for target in sorted(os.listdir(targets_dir)):
        target_dir = os.path.join(targets_dir, target)
        aliases_path = os.path.join(target_dir, 'aliases')
        files = sorted(os.listdir(target_dir))

        # aliases already defined
        if os.path.exists(aliases_path):
            continue

        # don't require aliases for support directories
        if any(os.path.splitext(f)[0] == 'test' and os.access(os.path.join(target_dir, f), os.X_OK) for f in files):
            continue

        # don't require aliases for setup_ directories
        if target.startswith('setup_'):
            continue

        # don't require aliases for prepare_ directories
        if target.startswith('prepare_'):
            continue

        # TODO: remove this exclusion once the `ansible-test network-integration` command is working properly
        # don't require aliases for network modules
        if any(target.startswith('%s_' % prefix) for prefix in network_prefixes):
            continue

        print('%s: missing integration test `aliases` file' % aliases_path)


if __name__ == '__main__':
    main()
