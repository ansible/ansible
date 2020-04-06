"""Payload management for sending Ansible files and test content to other systems (VMs, containers)."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import os
import stat
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
    filters = {}

    def make_executable(tar_info):  # type: (tarfile.TarInfo) -> t.Optional[tarfile.TarInfo]
        """Make the given file executable."""
        tar_info.mode |= stat.S_IXUSR | stat.S_IXOTH | stat.S_IXGRP
        return tar_info

    if not ANSIBLE_SOURCE_ROOT:
        # reconstruct the bin directory which is not available when running from an ansible install
        files.extend(create_temporary_bin_files(args))
        filters.update(dict((path[3:], make_executable) for path in ANSIBLE_BIN_SYMLINK_MAP.values() if path.startswith('../')))

    if not data_context().content.is_ansible:
        # exclude unnecessary files when not testing ansible itself
        files = [f for f in files if
                 is_subdir(f[1], 'bin/') or
                 is_subdir(f[1], 'lib/ansible/') or
                 (is_subdir(f[1], 'test/lib/ansible_test/') and not is_subdir(f[1], 'test/lib/ansible_test/tests/'))]

        if not isinstance(args, (ShellConfig, IntegrationConfig)):
            # exclude built-in ansible modules when they are not needed
            files = [f for f in files if not is_subdir(f[1], 'lib/ansible/modules/') or f[1] == 'lib/ansible/modules/__init__.py']

        collection_layouts = data_context().create_collection_layouts()

        for layout in collection_layouts:
            # include files from each collection in the same collection root as the content being tested
            files.extend((os.path.join(layout.root, path), os.path.join(layout.collection.directory, path)) for path in layout.all_files())

    for callback in data_context().payload_callbacks:
        callback(files)

    # maintain predictable file order
    files = sorted(set(files))

    display.info('Creating a payload archive containing %d files...' % len(files), verbosity=1)

    start = time.time()

    with tarfile.TarFile.open(dst_path, mode='w:gz', compresslevel=4, format=tarfile.GNU_FORMAT) as tar:
        for src, dst in files:
            display.info('%s -> %s' % (src, dst), verbosity=4)
            tar.add(src, dst, filter=filters.get(dst))

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
            os.symlink(dest, path)

    return tuple((os.path.join(temp_path, name), os.path.join('bin', name)) for name in sorted(ANSIBLE_BIN_SYMLINK_MAP))
