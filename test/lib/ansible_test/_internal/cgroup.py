"""Linux control group constants, classes and utilities."""

from __future__ import annotations

import codecs
import dataclasses
import pathlib
import re


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
    def root_path(self) -> pathlib.PurePosixPath:
        """The root path for this cgroup subsystem."""
        return pathlib.PurePosixPath(CGroupPath.ROOT, self.subsystem)

    @property
    def full_path(self) -> pathlib.PurePosixPath:
        """The full path for this cgroup subsystem."""
        return pathlib.PurePosixPath(self.root_path, str(self.path).lstrip('/'))

    @classmethod
    def parse(cls, value: str) -> CGroupEntry:
        """Parse the given cgroup line from the proc filesystem and return a cgroup entry."""
        cid, subsystem, path = value.split(':', maxsplit=2)

        return cls(
            id=int(cid),
            subsystem=subsystem.removeprefix('name='),
            path=pathlib.PurePosixPath(path),
        )

    @classmethod
    def loads(cls, value: str) -> tuple[CGroupEntry, ...]:
        """Parse the given output from the proc filesystem and return a tuple of cgroup entries."""
        return tuple(cls.parse(line) for line in value.splitlines())


@dataclasses.dataclass(frozen=True)
class MountEntry:
    """A single mount info entry parsed from '/proc/{pid}/mountinfo' in the proc filesystem."""

    mount_id: int
    parent_id: int
    device_major: int
    device_minor: int
    root: pathlib.PurePosixPath
    path: pathlib.PurePosixPath
    options: tuple[str, ...]
    fields: tuple[str, ...]
    type: str
    source: pathlib.PurePosixPath
    super_options: tuple[str, ...]

    @classmethod
    def parse(cls, value: str) -> MountEntry:
        """Parse the given mount info line from the proc filesystem and return a mount entry."""
        # See: https://man7.org/linux/man-pages/man5/proc.5.html
        # See: https://github.com/torvalds/linux/blob/aea23e7c464bfdec04b52cf61edb62030e9e0d0a/fs/proc_namespace.c#L135
        mount_id, parent_id, device_major_minor, root, path, options, *remainder = value.split(' ')
        fields = remainder[:-4]
        separator, mtype, source, super_options = remainder[-4:]

        assert separator == '-'

        device_major, device_minor = device_major_minor.split(':')

        return cls(
            mount_id=int(mount_id),
            parent_id=int(parent_id),
            device_major=int(device_major),
            device_minor=int(device_minor),
            root=_decode_path(root),
            path=_decode_path(path),
            options=tuple(options.split(',')),
            fields=tuple(fields),
            type=mtype,
            source=_decode_path(source),
            super_options=tuple(super_options.split(',')),
        )

    @classmethod
    def loads(cls, value: str) -> tuple[MountEntry, ...]:
        """Parse the given output from the proc filesystem and return a tuple of mount info entries."""
        return tuple(cls.parse(line) for line in value.splitlines())


def _decode_path(value: str) -> pathlib.PurePosixPath:
    """Decode and return a path which may contain octal escape sequences."""
    # See: https://github.com/torvalds/linux/blob/aea23e7c464bfdec04b52cf61edb62030e9e0d0a/fs/proc_namespace.c#L150
    path = re.sub(r'(\\[0-7]{3})', lambda m: codecs.decode(m.group(0).encode('ascii'), 'unicode_escape'), value)
    return pathlib.PurePosixPath(path)
