"""Linux control group constants, classes and utilities."""
from __future__ import annotations

import dataclasses
import pathlib


class CGroupPath:
    """Linux cgroup path constants."""
    ROOT = '/sys/fs/cgroup'
    SYSTEMD = '/sys/fs/cgroup/systemd'
    SYSTEMD_RELEASE_AGENT = '/sys/fs/cgroup/systemd/release_agent'


class MountType:
    """Linux filesystem mount type constants."""
    TMPFS = 'tmpfs'
    CGROUP_V1 = 'cgroup'
    CGROUP_V2 = 'cgroup2'


@dataclasses.dataclass(frozen=True)
class CGroupEntry:
    """A single cgroup entry parsed from '/proc/{pid}/cgroup' in the proc filesystem."""
    id: int
    subsystem: str
    path: pathlib.PurePosixPath

    @property
    def root_path(self):
        """The root path for this cgroup subsystem."""
        return pathlib.PurePosixPath(CGroupPath.ROOT, self.subsystem)

    @property
    def full_path(self) -> pathlib.PurePosixPath:
        """The full path for this cgroup subsystem."""
        return pathlib.PurePosixPath(self.root_path, str(self.path).lstrip('/'))

    @classmethod
    def parse(cls, value: str) -> CGroupEntry:
        """Parse the given cgroup line from the proc filesystem and return a cgroup entry."""
        cid, subsystem, path = value.split(':')

        return cls(
            id=int(cid),
            subsystem=subsystem.removeprefix('name='),
            path=pathlib.PurePosixPath(path)
        )

    @classmethod
    def loads(cls, value: str) -> tuple[CGroupEntry, ...]:
        """Parse the given output from the proc filesystem and return a tuple of cgroup entries."""
        return tuple(cls.parse(line) for line in value.splitlines())


@dataclasses.dataclass(frozen=True)
class MountEntry:
    """A single mount entry parsed from '/proc/{pid}/mounts' in the proc filesystem."""
    device: pathlib.PurePosixPath
    path: pathlib.PurePosixPath
    type: str
    options: tuple[str, ...]

    @classmethod
    def parse(cls, value: str) -> MountEntry:
        """Parse the given mount line from the proc filesystem and return a mount entry."""
        device, path, mtype, options, _a, _b = value.split(' ')

        return cls(
            device=pathlib.PurePosixPath(device),
            path=pathlib.PurePosixPath(path),
            type=mtype,
            options=tuple(options.split(',')),
        )

    @classmethod
    def loads(cls, value: str) -> tuple[MountEntry, ...]:
        """Parse the given output from the proc filesystem and return a tuple of mount entries."""
        return tuple(cls.parse(line) for line in value.splitlines())
