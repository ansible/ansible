"""Loading, parsing and storing of completion configurations."""
from __future__ import annotations

import abc
import dataclasses
import os
import typing as t

from .constants import (
    CONTROLLER_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from .util import (
    ANSIBLE_TEST_DATA_ROOT,
    cache,
    read_lines_without_comments,
)

from .data import (
    data_context,
)

from .become import (
    SUPPORTED_BECOME_METHODS,
)


@dataclasses.dataclass(frozen=True)
class CompletionConfig(metaclass=abc.ABCMeta):
    """Base class for completion configuration."""
    name: str

    @property
    @abc.abstractmethod
    def is_default(self):
        """True if the completion entry is only used for defaults, otherwise False."""


@dataclasses.dataclass(frozen=True)
class PosixCompletionConfig(CompletionConfig, metaclass=abc.ABCMeta):
    """Base class for completion configuration of POSIX environments."""
    @property
    @abc.abstractmethod
    def supported_pythons(self) -> list[str]:
        """Return a list of the supported Python versions."""

    @abc.abstractmethod
    def get_python_path(self, version: str) -> str:
        """Return the path of the requested Python version."""

    def get_default_python(self, controller: bool) -> str:
        """Return the default Python version for a controller or target as specified."""
        context_pythons = CONTROLLER_PYTHON_VERSIONS if controller else SUPPORTED_PYTHON_VERSIONS
        version = [python for python in self.supported_pythons if python in context_pythons][0]
        return version

    @property
    def controller_supported(self) -> bool:
        """True if at least one Python version is provided which supports the controller, otherwise False."""
        return any(version in CONTROLLER_PYTHON_VERSIONS for version in self.supported_pythons)


@dataclasses.dataclass(frozen=True)
class PythonCompletionConfig(PosixCompletionConfig, metaclass=abc.ABCMeta):
    """Base class for completion configuration of Python environments."""
    python: str = ''
    python_dir: str = '/usr/bin'

    @property
    def supported_pythons(self) -> list[str]:
        """Return a list of the supported Python versions."""
        versions = self.python.split(',') if self.python else []
        versions = [version for version in versions if version in SUPPORTED_PYTHON_VERSIONS]
        return versions

    def get_python_path(self, version: str) -> str:
        """Return the path of the requested Python version."""
        return os.path.join(self.python_dir, f'python{version}')


@dataclasses.dataclass(frozen=True)
class RemoteCompletionConfig(CompletionConfig):
    """Base class for completion configuration of remote environments provisioned through Ansible Core CI."""
    provider: t.Optional[str] = None
    arch: t.Optional[str] = None

    @property
    def platform(self):
        """The name of the platform."""
        return self.name.partition('/')[0]

    @property
    def version(self):
        """The version of the platform."""
        return self.name.partition('/')[2]

    @property
    def is_default(self):
        """True if the completion entry is only used for defaults, otherwise False."""
        return not self.version

    def __post_init__(self):
        if not self.provider:
            raise Exception(f'Remote completion entry "{self.name}" must provide a "provider" setting.')

        if not self.arch:
            raise Exception(f'Remote completion entry "{self.name}" must provide a "arch" setting.')


@dataclasses.dataclass(frozen=True)
class InventoryCompletionConfig(CompletionConfig):
    """Configuration for inventory files."""
    def __init__(self) -> None:
        super().__init__(name='inventory')

    @property
    def is_default(self) -> bool:
        """True if the completion entry is only used for defaults, otherwise False."""
        return False


@dataclasses.dataclass(frozen=True)
class PosixSshCompletionConfig(PythonCompletionConfig):
    """Configuration for a POSIX host reachable over SSH."""
    def __init__(self, user: str, host: str) -> None:
        super().__init__(
            name=f'{user}@{host}',
            python=','.join(SUPPORTED_PYTHON_VERSIONS),
        )

    @property
    def is_default(self) -> bool:
        """True if the completion entry is only used for defaults, otherwise False."""
        return False


@dataclasses.dataclass(frozen=True)
class DockerCompletionConfig(PythonCompletionConfig):
    """Configuration for Docker containers."""
    image: str = ''
    seccomp: str = 'default'
    placeholder: bool = False

    @property
    def is_default(self):
        """True if the completion entry is only used for defaults, otherwise False."""
        return False

    def __post_init__(self):
        if not self.image:
            raise Exception(f'Docker completion entry "{self.name}" must provide an "image" setting.')

        if not self.supported_pythons and not self.placeholder:
            raise Exception(f'Docker completion entry "{self.name}" must provide a "python" setting.')


@dataclasses.dataclass(frozen=True)
class NetworkRemoteCompletionConfig(RemoteCompletionConfig):
    """Configuration for remote network platforms."""
    collection: str = ''
    connection: str = ''
    placeholder: bool = False

    def __post_init__(self):
        if not self.placeholder:
            super().__post_init__()


@dataclasses.dataclass(frozen=True)
class PosixRemoteCompletionConfig(RemoteCompletionConfig, PythonCompletionConfig):
    """Configuration for remote POSIX platforms."""
    become: t.Optional[str] = None
    placeholder: bool = False

    def __post_init__(self):
        if not self.placeholder:
            super().__post_init__()

        if self.become and self.become not in SUPPORTED_BECOME_METHODS:
            raise Exception(f'POSIX remote completion entry "{self.name}" setting "become" must be omitted or one of: {", ".join(SUPPORTED_BECOME_METHODS)}')

        if not self.supported_pythons:
            if self.version and not self.placeholder:
                raise Exception(f'POSIX remote completion entry "{self.name}" must provide a "python" setting.')
        else:
            if not self.version:
                raise Exception(f'POSIX remote completion entry "{self.name}" is a platform default and cannot provide a "python" setting.')


@dataclasses.dataclass(frozen=True)
class WindowsRemoteCompletionConfig(RemoteCompletionConfig):
    """Configuration for remote Windows platforms."""


TCompletionConfig = t.TypeVar('TCompletionConfig', bound=CompletionConfig)


def load_completion(name: str, completion_type: t.Type[TCompletionConfig]) -> dict[str, TCompletionConfig]:
    """Load the named completion entries, returning them in dictionary form using the specified completion type."""
    lines = read_lines_without_comments(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'completion', '%s.txt' % name), remove_blank_lines=True)

    if data_context().content.collection:
        context = 'collection'
    else:
        context = 'ansible-core'

    items = {name: data for name, data in [parse_completion_entry(line) for line in lines] if data.get('context', context) == context}

    for item in items.values():
        item.pop('context', None)
        item.pop('placeholder', None)

    completion = {name: completion_type(name=name, **data) for name, data in items.items()}

    return completion


def parse_completion_entry(value: str) -> tuple[str, dict[str, str]]:
    """Parse the given completion entry, returning the entry name and a dictionary of key/value settings."""
    values = value.split()

    name = values[0]
    data = {kvp[0]: kvp[1] if len(kvp) > 1 else '' for kvp in [item.split('=', 1) for item in values[1:]]}

    return name, data


def filter_completion(
        completion: dict[str, TCompletionConfig],
        controller_only: bool = False,
        include_defaults: bool = False,
) -> dict[str, TCompletionConfig]:
    """Return the given completion dictionary, filtering out configs which do not support the controller if controller_only is specified."""
    if controller_only:
        completion = {name: config for name, config in completion.items() if isinstance(config, PosixCompletionConfig) and config.controller_supported}

    if not include_defaults:
        completion = {name: config for name, config in completion.items() if not config.is_default}

    return completion


@cache
def docker_completion() -> dict[str, DockerCompletionConfig]:
    """Return docker completion entries."""
    return load_completion('docker', DockerCompletionConfig)


@cache
def remote_completion() -> dict[str, PosixRemoteCompletionConfig]:
    """Return remote completion entries."""
    return load_completion('remote', PosixRemoteCompletionConfig)


@cache
def windows_completion() -> dict[str, WindowsRemoteCompletionConfig]:
    """Return windows completion entries."""
    return load_completion('windows', WindowsRemoteCompletionConfig)


@cache
def network_completion() -> dict[str, NetworkRemoteCompletionConfig]:
    """Return network completion entries."""
    return load_completion('network', NetworkRemoteCompletionConfig)
