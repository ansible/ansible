"""Payload management for sending Ansible files and test content to other systems (VMs, containers)."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tarfile
import time

from .config import (
    IntegrationConfig,
    ShellConfig,
)

from .util import (
    display,
    ANSIBLE_ROOT,
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


def create_payload(args, dst_path):  # type: (CommonConfig, str) -> None
    """Create a payload for delegation."""
    if args.explain:
        return

    files = [(os.path.join(ANSIBLE_ROOT, path), path) for path in data_context().install.all_files()]

    if not data_context().content.is_ansible:
        files = [f for f in files if
                 f[1].startswith('bin/') or
                 f[1].startswith('lib/') or
                 f[1].startswith('test/lib/') or
                 f[1].startswith('packaging/requirements/') or
                 f[1] in (
                     'setup.py',
                     'README.rst',
                     'requirements.txt',
                     # units only
                     'test/units/ansible.cfg',
                     # integration only
                     'test/integration/integration.cfg',
                     'test/integration/integration_config.yml',
                     'test/integration/inventory',
                 )]

        if not isinstance(args, (ShellConfig, IntegrationConfig)):
            files = [f for f in files if not f[1].startswith('lib/ansible/modules/') or f[1] == 'lib/ansible/modules/__init__.py']

    if data_context().content.collection:
        files.extend((os.path.join(data_context().content.root, path), os.path.join(data_context().content.collection.directory, path))
                     for path in data_context().content.all_files())

    for callback in data_context().payload_callbacks:
        callback(files)

    display.info('Creating a payload archive containing %d files...' % len(files), verbosity=1)

    start = time.time()

    with tarfile.TarFile.gzopen(dst_path, mode='w', compresslevel=4) as tar:
        for src, dst in files:
            display.info('%s -> %s' % (src, dst), verbosity=4)
            tar.add(src, dst)

    duration = time.time() - start
    payload_size_bytes = os.path.getsize(dst_path)

    display.info('Created a %d byte payload archive containing %d files in %d seconds.' % (payload_size_bytes, len(files), duration), verbosity=1)
