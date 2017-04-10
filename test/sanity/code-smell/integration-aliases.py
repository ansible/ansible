#!/usr/bin/env python

import os
import textwrap


def main():
    targets_dir = 'test/integration/targets'

    with open('test/integration/target-prefixes.network', 'r') as prefixes_fd:
        network_prefixes = prefixes_fd.read().splitlines()

    missing_aliases = []

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

        missing_aliases.append(target_dir)

    if missing_aliases:
        message = textwrap.dedent('''
        The following integration target directories are missing `aliases` files:

        %s

        If these tests cannot be run as part of CI (requires external services, unsupported dependencies, etc.),
        then they most likely belong in `test/integration/roles/` instead of `test/integration/targets/`.
        In that case, do not add an `aliases` file. Instead, just relocate the tests.

        However, if you think that the tests should be able to be supported by CI, please discuss test
        organization with @mattclay or @gundalow on GitHub or #ansible-devel on IRC.

        If these tests can be run as part of CI, you'll need to add an appropriate CI alias, such as:

        posix/ci/group1
        windows/ci/group2

        The CI groups are used to balance tests across multiple jobs to minimize test run time.
        Using the relevant `group1` entry is fine in most cases. Groups can be changed later to redistribute tests.

        Aliases can also be used to express test requirements:

        needs/privileged
        needs/root
        needs/ssh

        Other aliases are used to skip tests under certain conditions:

        skip/freebsd
        skip/osx
        skip/python3

        Take a look at existing `aliases` files to see what aliases are available and how they're used.
        ''').strip() % '\n'.join(missing_aliases)

        print(message)

        exit(1)


if __name__ == '__main__':
    main()
