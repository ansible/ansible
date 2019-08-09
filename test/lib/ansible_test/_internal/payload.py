"""Payload management for sending Ansible files and test content to other systems (VMs, containers)."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import os
import tarfile
import tempfile
import time

from . import types as t

from .config import (
    IntegrationConfig,
    ShellConfig,
)

from .util import (
    display,
    ANSIBLE_ROOT,
    ANSIBLE_SOURCE_ROOT,
    remove_tree,
    is_subdir,
)

from .data import (
    data_context,
)

from .util_common import (
    CommonConfig,
)

# improve performance by disabling uid/gid lookups
tarfile.pwd = None
tarfile.grp = None

# this bin symlink map must exactly match the contents of the bin directory
# it is necessary for payload creation to reconstruct the bin directory when running ansible-test from an installed version of ansible
ANSIBLE_BIN_SYMLINK_MAP = {
    'ansible': '../lib/ansible/cli/scripts/ansible_cli_stub.py',
    'ansible-config': 'ansible',
    'ansible-connection': '../lib/ansible/cli/scripts/ansible_connection_cli_stub.py',
    'ansible-console': 'ansible',
    'ansible-doc': 'ansible',
    'ansible-galaxy': 'ansible',
    'ansible-inventory': 'ansible',
    'ansible-playbook': 'ansible',
    'ansible-pull': 'ansible',
    'ansible-test': '../test/lib/ansible_test/_data/cli/ansible_test_cli_stub.py',
    'ansible-vault': 'ansible',
}


def create_payload(args, dst_path):  # type: (CommonConfig, str) -> None
    """Create a payload for delegation."""
    if args.explain:
        return

    files = list(data_context().ansible_source)

    if not ANSIBLE_SOURCE_ROOT:
        # reconstruct the bin directory which is not available when running from an ansible install
        files.extend(create_temporary_bin_files(args))

    if not data_context().content.is_ansible:
        # exclude unnecessary files when not testing ansible itself
        files = [f for f in files if
                 is_subdir(f[1], 'bin/') or
                 is_subdir(f[1], 'lib/ansible/') or
                 (is_subdir(f[1], 'test/lib/ansible_test/') and not is_subdir(f[1], 'test/lib/ansible_test/tests/'))]

        if not isinstance(args, (ShellConfig, IntegrationConfig)):
            # exclude built-in ansible modules when they are not needed
            files = [f for f in files if not is_subdir(f[1], 'lib/ansible/modules/') or f[1] == 'lib/ansible/modules/__init__.py']

        if data_context().content.collection:
            # include collections content for testing
            files.extend((os.path.join(data_context().content.root, path), os.path.join(data_context().content.collection.directory, path))
                         for path in data_context().content.all_files())

    # these files need to be migrated to the ansible-test data directory
    hack_files_to_keep = (
        'test/integration/integration.cfg',
        'test/integration/integration_config.yml',
        'test/integration/inventory',
        'test/integration/network-integration.cfg',
        'test/integration/target-prefixes.network',
        'test/integration/windows-integration.cfg',
    )

    # temporary solution to include files not yet present in the ansible-test data directory
    files.extend([(os.path.join(ANSIBLE_ROOT, path), path) for path in hack_files_to_keep])

    for callback in data_context().payload_callbacks:
        callback(files)

    # maintain predictable file order
    files = sorted(files)

    display.info('Creating a payload archive containing %d files...' % len(files), verbosity=1)

    start = time.time()

    with tarfile.TarFile.gzopen(dst_path, mode='w', compresslevel=4) as tar:
        for src, dst in files:
            display.info('%s -> %s' % (src, dst), verbosity=4)
            tar.add(src, dst)

    duration = time.time() - start
    payload_size_bytes = os.path.getsize(dst_path)

    display.info('Created a %d byte payload archive containing %d files in %d seconds.' % (payload_size_bytes, len(files), duration), verbosity=1)


def create_temporary_bin_files(args):  # type: (CommonConfig) -> t.Tuple[t.Tuple[str, str], ...]
    """Create a temporary ansible bin directory populated using the symlink map."""
    if args.explain:
        temp_path = '/tmp/ansible-tmp-bin'
    else:
        temp_path = tempfile.mkdtemp(prefix='ansible', suffix='bin')
        atexit.register(remove_tree, temp_path)

        for name, dest in ANSIBLE_BIN_SYMLINK_MAP.items():
            path = os.path.join(temp_path, name)
            os.link(dest, path)

    return tuple((os.path.join(temp_path, name), os.path.join('bin', name)) for name in sorted(ANSIBLE_BIN_SYMLINK_MAP))
