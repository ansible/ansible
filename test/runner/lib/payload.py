"""Payload management for sending Ansible files and test content to other systems (VMs, containers)."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from lib.config import (
    CommonConfig,
    EnvironmentConfig,
)

from lib.pytar import (
    AllowGitTarFilter,
    create_tarfile,
    DefaultTarFilter,
)


def create_payload(args, dst_path):  # type: (CommonConfig, str) -> None
    """Create a payload for delegation."""
    if args.explain:
        return

    if isinstance(args, EnvironmentConfig) and args.docker_keep_git:
        tar_filter = AllowGitTarFilter()
    else:
        tar_filter = DefaultTarFilter()

    create_tarfile(dst_path, '.', tar_filter)
