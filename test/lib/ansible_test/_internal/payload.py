"""Payload management for sending Ansible files and test content to other systems (VMs, containers)."""

from __future__ import annotations

import os
import stat
import tarfile
import tempfile
import time
import typing as t

from .constants import (
    ANSIBLE_BIN_SYMLINK_MAP,
)

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
    PayloadConfig,
)

from .util_common import (
    CommonConfig,
    ExitHandler,
)

# improve performance by disabling uid/gid lookups
tarfile.pwd = None  # type: ignore[attr-defined]  # undocumented attribute
tarfile.grp = None  # type: ignore[attr-defined]  # undocumented attribute


def create_payload(args: CommonConfig, dst_path: str) -> None:
    """Create a payload for delegation."""
    if args.explain:
        return

    files = list(data_context().ansible_source)
    permissions: dict[str, int] = {}
    filters: dict[str, t.Callable[[tarfile.TarInfo], t.Optional[tarfile.TarInfo]]] = {}

    # Exclude vendored files from the payload.
    # They may not be compatible with the delegated environment.
    files = [
        (abs_path, rel_path) for abs_path, rel_path in files
        if not rel_path.startswith('lib/ansible/_vendor/')
        or rel_path == 'lib/ansible/_vendor/__init__.py'
    ]

    def apply_permissions(tar_info: tarfile.TarInfo, mode: int) -> t.Optional[tarfile.TarInfo]:
        """
        Apply the specified permissions to the given file.
        Existing file type bits are preserved.
        """
        tar_info.mode &= ~(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        tar_info.mode |= mode

        return tar_info

    def make_executable(tar_info: tarfile.TarInfo) -> t.Optional[tarfile.TarInfo]:
        """
        Make the given file executable and readable by all, and writeable by the owner.
        Existing file type bits are preserved.
        This ensures consistency of test results when using unprivileged users.
        """
        return apply_permissions(
            tar_info,
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |
            stat.S_IWUSR
        )  # fmt: skip

    def make_non_executable(tar_info: tarfile.TarInfo) -> t.Optional[tarfile.TarInfo]:
        """
        Make the given file readable by all, and writeable by the owner.
        Existing file type bits are preserved.
        This ensures consistency of test results when using unprivileged users.
        """
        return apply_permissions(
            tar_info,
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
            stat.S_IWUSR
        )  # fmt: skip

    def detect_permissions(tar_info: tarfile.TarInfo) -> t.Optional[tarfile.TarInfo]:
        """
        Detect and apply the appropriate permissions for a file.
        Existing file type bits are preserved.
        This ensures consistency of test results when using unprivileged users.
        """
        if tar_info.path.startswith('ansible/'):
            mode = permissions.get(os.path.relpath(tar_info.path, 'ansible'))
        elif data_context().content.collection and is_subdir(tar_info.path, data_context().content.collection.directory):
            mode = permissions.get(os.path.relpath(tar_info.path, data_context().content.collection.directory))
        else:
            mode = None

        if mode:
            tar_info = apply_permissions(tar_info, mode)
        elif tar_info.mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            # If any execute bit is set, treat the file as executable.
            # This ensures that sanity tests which check execute bits behave correctly.
            tar_info = make_executable(tar_info)
        else:
            tar_info = make_non_executable(tar_info)

        return tar_info

    if not ANSIBLE_SOURCE_ROOT:
        # reconstruct the bin directory which is not available when running from an ansible install
        files.extend(create_temporary_bin_files(args))
        filters.update(dict((os.path.join('ansible', path[3:]), make_executable) for path in ANSIBLE_BIN_SYMLINK_MAP.values() if path.startswith('../')))

    if not data_context().content.is_ansible:
        # exclude unnecessary files when not testing ansible itself
        files = [f for f in files if
                 is_subdir(f[1], 'bin/') or
                 is_subdir(f[1], 'lib/ansible/') or
                 is_subdir(f[1], 'test/lib/ansible_test/')]

        if not isinstance(args, (ShellConfig, IntegrationConfig)):
            # exclude built-in ansible modules when they are not needed
            files = [f for f in files if not is_subdir(f[1], 'lib/ansible/modules/') or f[1] == 'lib/ansible/modules/__init__.py']

        collection_layouts = data_context().create_collection_layouts()

        content_files: list[tuple[str, str]] = []
        extra_files: list[tuple[str, str]] = []

        for layout in collection_layouts:
            if layout == data_context().content:
                # include files from the current collection (layout.collection.directory will be added later)
                content_files.extend((os.path.join(layout.root, path), path) for path in data_context().content.all_files())
            else:
                # include files from each collection in the same collection root as the content being tested
                extra_files.extend((os.path.join(layout.root, path), os.path.join(layout.collection.directory, path)) for path in layout.all_files())
    else:
        # when testing ansible itself the ansible source is the content
        content_files = files
        # there are no extra files when testing ansible itself
        extra_files = []

    payload_config = PayloadConfig(
        files=content_files,
        permissions=permissions,
    )

    for callback in data_context().payload_callbacks:
        # execute callbacks only on the content paths
        # this is done before placing them in the appropriate subdirectory (see below)
        callback(payload_config)

    # place ansible source files under the 'ansible' directory on the delegated host
    files = [(src, os.path.join('ansible', dst)) for src, dst in files]

    if data_context().content.collection:
        # place collection files under the 'ansible_collections/{namespace}/{collection}' directory on the delegated host
        files.extend((src, os.path.join(data_context().content.collection.directory, dst)) for src, dst in content_files)
        # extra files already have the correct destination path
        files.extend(extra_files)

    # maintain predictable file order
    files = sorted(set(files))

    display.info('Creating a payload archive containing %d files...' % len(files), verbosity=1)

    start = time.time()

    with tarfile.open(dst_path, mode='w:gz', compresslevel=4, format=tarfile.GNU_FORMAT) as tar:
        for src, dst in files:
            display.info('%s -> %s' % (src, dst), verbosity=4)
            tar.add(src, dst, filter=filters.get(dst, detect_permissions))

    duration = time.time() - start
    payload_size_bytes = os.path.getsize(dst_path)

    display.info('Created a %d byte payload archive containing %d files in %d seconds.' % (payload_size_bytes, len(files), duration), verbosity=1)


def create_temporary_bin_files(args: CommonConfig) -> tuple[tuple[str, str], ...]:
    """Create a temporary ansible bin directory populated using the symlink map."""
    if args.explain:
        temp_path = '/tmp/ansible-tmp-bin'
    else:
        temp_path = tempfile.mkdtemp(prefix='ansible', suffix='bin')
        ExitHandler.register(remove_tree, temp_path)

        for name, dest in ANSIBLE_BIN_SYMLINK_MAP.items():
            path = os.path.join(temp_path, name)
            os.symlink(dest, path)

    return tuple((os.path.join(temp_path, name), os.path.join('bin', name)) for name in sorted(ANSIBLE_BIN_SYMLINK_MAP))
