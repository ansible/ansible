"""Diagnostic utilities to probe container cgroup behavior during development and testing (both manual and integration)."""
from __future__ import annotations

import dataclasses
import enum
import json
import os
import pathlib
import pwd
import typing as t

from ..io import (
    read_text_file,
    write_text_file,
)

from ..util import (
    display,
    ANSIBLE_TEST_TARGET_ROOT,
)

from ..config import (
    EnvironmentConfig,
)

from ..docker_util import (
    LOGINUID_NOT_SET,
    docker_exec,
    get_docker_info,
    get_podman_remote,
    require_docker,
)

from ..host_configs import (
    DockerConfig,
)

from ..cgroup import (
    CGroupEntry,
    CGroupPath,
    MountEntry,
    MountType,
)


class CGroupState(enum.Enum):
    """The expected state of a cgroup related mount point."""

    HOST = enum.auto()
    PRIVATE = enum.auto()
    SHADOWED = enum.auto()


@dataclasses.dataclass(frozen=True)
class CGroupMount:
    """Details on a cgroup mount point that is expected to be present in the container."""

    path: str
    type: t.Optional[str]
    writable: t.Optional[bool]
    state: t.Optional[CGroupState]

    def __post_init__(self):
        assert pathlib.PurePosixPath(self.path).is_relative_to(CGroupPath.ROOT)

        if self.type is None:
            assert self.state is None
        elif self.type == MountType.TMPFS:
            assert self.writable is True
            assert self.state is None
        else:
            assert self.type in (MountType.CGROUP_V1, MountType.CGROUP_V2)
            assert self.state is not None


def check_container_cgroup_status(args: EnvironmentConfig, config: DockerConfig, container_name: str, expected_mounts: tuple[CGroupMount, ...]) -> None:
    """Check the running container to examine the state of the cgroup hierarchies."""
    cmd = ['sh', '-c', 'cat /proc/1/cgroup && echo && cat /proc/1/mountinfo']

    stdout = docker_exec(args, container_name, cmd, capture=True)[0]
    cgroups_stdout, mounts_stdout = stdout.split('\n\n')

    cgroups = CGroupEntry.loads(cgroups_stdout)
    mounts = MountEntry.loads(mounts_stdout)

    mounts = tuple(mount for mount in mounts if mount.path.is_relative_to(CGroupPath.ROOT))

    mount_cgroups: dict[MountEntry, CGroupEntry] = {}
    probe_paths: dict[pathlib.PurePosixPath, t.Optional[str]] = {}

    for cgroup in cgroups:
        if cgroup.subsystem:
            mount = ([mount for mount in mounts if
                      mount.type == MountType.CGROUP_V1 and
                      mount.path.is_relative_to(cgroup.root_path) and
                      cgroup.full_path.is_relative_to(mount.path)
                      ] or [None])[-1]
        else:
            mount = ([mount for mount in mounts if
                      mount.type == MountType.CGROUP_V2 and
                      mount.path == cgroup.root_path
                      ] or [None])[-1]

        if mount:
            mount_cgroups[mount] = cgroup

    for mount in mounts:
        probe_paths[mount.path] = None

        if (cgroup := mount_cgroups.get(mount)) and cgroup.full_path != mount.path:  # child of mount.path
            probe_paths[cgroup.full_path] = None

    probe_script = read_text_file(os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'probe_cgroups.py'))
    probe_command = [config.python.path, '-', f'{container_name}-probe'] + [str(path) for path in probe_paths]
    probe_results = json.loads(docker_exec(args, container_name, probe_command, capture=True, data=probe_script)[0])

    for path in probe_paths:
        probe_paths[path] = probe_results[str(path)]

    remaining_mounts: dict[pathlib.PurePosixPath, MountEntry] = {mount.path: mount for mount in mounts}
    results: dict[pathlib.PurePosixPath, tuple[bool, str]] = {}

    for expected_mount in expected_mounts:
        expected_path = pathlib.PurePosixPath(expected_mount.path)

        if not (actual_mount := remaining_mounts.pop(expected_path, None)):
            results[expected_path] = (False, 'not mounted')
            continue

        actual_mount_write_error = probe_paths[actual_mount.path]
        actual_mount_errors = []

        if cgroup := mount_cgroups.get(actual_mount):
            if expected_mount.state == CGroupState.SHADOWED:
                actual_mount_errors.append('unexpected cgroup association')

            if cgroup.root_path == cgroup.full_path and expected_mount.state == CGroupState.HOST:
                results[cgroup.root_path.joinpath('???')] = (False, 'missing cgroup')

            if cgroup.full_path == actual_mount.path:
                if cgroup.root_path != cgroup.full_path and expected_mount.state == CGroupState.PRIVATE:
                    actual_mount_errors.append('unexpected mount')
            else:
                cgroup_write_error = probe_paths[cgroup.full_path]
                cgroup_errors = []

                if expected_mount.state == CGroupState.SHADOWED:
                    cgroup_errors.append('unexpected cgroup association')

                if cgroup.root_path != cgroup.full_path and expected_mount.state == CGroupState.PRIVATE:
                    cgroup_errors.append('unexpected cgroup')

                if cgroup_write_error:
                    cgroup_errors.append(cgroup_write_error)

                if cgroup_errors:
                    results[cgroup.full_path] = (False, f'directory errors: {", ".join(cgroup_errors)}')
                else:
                    results[cgroup.full_path] = (True, 'directory (writable)')
        elif expected_mount.state not in (None, CGroupState.SHADOWED):
            actual_mount_errors.append('missing cgroup association')

        if actual_mount.type != expected_mount.type and expected_mount.type is not None:
            actual_mount_errors.append(f'type not {expected_mount.type}')

        if bool(actual_mount_write_error) == expected_mount.writable:
            actual_mount_errors.append(f'{actual_mount_write_error or "writable"}')

        if actual_mount_errors:
            results[actual_mount.path] = (False, f'{actual_mount.type} errors: {", ".join(actual_mount_errors)}')
        else:
            results[actual_mount.path] = (True, f'{actual_mount.type} ({actual_mount_write_error or "writable"})')

    for remaining_mount in remaining_mounts.values():
        remaining_mount_write_error = probe_paths[remaining_mount.path]

        results[remaining_mount.path] = (False, f'unexpected {remaining_mount.type} mount ({remaining_mount_write_error or "writable"})')

    identity = get_identity(args, config, container_name)
    messages: list[tuple[pathlib.PurePosixPath, bool, str]] = [(path, result[0], result[1]) for path, result in sorted(results.items())]
    message = '\n'.join(f'{"PASS" if result else "FAIL"}: {path} -> {message}' for path, result, message in messages)

    display.info(f'>>> Container: {identity}\n{message.rstrip()}')

    if args.dev_probe_cgroups:
        write_text_file(os.path.join(args.dev_probe_cgroups, f'{identity}.log'), message)


def get_identity(args: EnvironmentConfig, config: DockerConfig, container_name: str) -> str:
    """Generate and return an identity string to use when logging test results."""
    engine = require_docker().command

    try:
        loginuid = int(read_text_file('/proc/self/loginuid'))
    except FileNotFoundError:
        loginuid = LOGINUID_NOT_SET

    user = pwd.getpwuid(os.getuid()).pw_name
    login_user = user if loginuid == LOGINUID_NOT_SET else pwd.getpwuid(loginuid).pw_name
    remote = engine == 'podman' and get_podman_remote()

    tags = (
        config.name,
        engine,
        f'cgroup={config.cgroup.value}@{get_docker_info(args).cgroup_version}',
        f'remote={remote}',
        f'user={user}',
        f'loginuid={login_user}',
        container_name,
    )

    return '|'.join(tags)
