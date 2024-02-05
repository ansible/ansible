"""Configuration for the test hosts requested by the user."""
from __future__ import annotations

import abc
import dataclasses
import enum
import os
import pickle
import sys
import typing as t

from .constants import (
    SUPPORTED_PYTHON_VERSIONS,
)

from .io import (
    open_binary_file,
)

from .completion import (
    AuditMode,
    CGroupVersion,
    CompletionConfig,
    docker_completion,
    DockerCompletionConfig,
    InventoryCompletionConfig,
    network_completion,
    NetworkRemoteCompletionConfig,
    PosixCompletionConfig,
    PosixRemoteCompletionConfig,
    PosixSshCompletionConfig,
    remote_completion,
    RemoteCompletionConfig,
    windows_completion,
    WindowsRemoteCompletionConfig,
    filter_completion,
)

from .util import (
    find_python,
    get_available_python_versions,
    str_to_version,
    version_to_str,
    Architecture,
)


@dataclasses.dataclass(frozen=True)
class OriginCompletionConfig(PosixCompletionConfig):
    """Pseudo completion config for the origin."""

    def __init__(self) -> None:
        super().__init__(name='origin')

    @property
    def supported_pythons(self) -> list[str]:
        """Return a list of the supported Python versions."""
        current_version = version_to_str(sys.version_info[:2])
        versions = [version for version in SUPPORTED_PYTHON_VERSIONS if version == current_version] + \
                   [version for version in SUPPORTED_PYTHON_VERSIONS if version != current_version]
        return versions

    def get_python_path(self, version: str) -> str:
        """Return the path of the requested Python version."""
        version = find_python(version)
        return version

    @property
    def is_default(self) -> bool:
        """True if the completion entry is only used for defaults, otherwise False."""
        return False


@dataclasses.dataclass(frozen=True)
class HostContext:
    """Context used when getting and applying defaults for host configurations."""

    controller_config: t.Optional['PosixConfig']

    @property
    def controller(self) -> bool:
        """True if the context is for the controller, otherwise False."""
        return not self.controller_config


@dataclasses.dataclass
class HostConfig(metaclass=abc.ABCMeta):
    """Base class for host configuration."""

    @abc.abstractmethod
    def get_defaults(self, context: HostContext) -> CompletionConfig:
        """Return the default settings."""

    @abc.abstractmethod
    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""

    @property
    def is_managed(self) -> bool:
        """
        True if the host is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have destructive operations performed without explicit permission from the user.
        """
        return False


@dataclasses.dataclass
class PythonConfig(metaclass=abc.ABCMeta):
    """Configuration for Python."""

    version: t.Optional[str] = None
    path: t.Optional[str] = None

    @property
    def tuple(self) -> tuple[int, ...]:
        """Return the Python version as a tuple."""
        return str_to_version(self.version)

    @property
    def major_version(self) -> int:
        """Return the Python major version."""
        return self.tuple[0]

    def apply_defaults(self, context: HostContext, defaults: PosixCompletionConfig) -> None:
        """Apply default settings."""
        if self.version in (None, 'default'):
            self.version = defaults.get_default_python(context.controller)

        if self.path:
            if self.path.endswith('/'):
                self.path = os.path.join(self.path, f'python{self.version}')

            # FUTURE: If the host is origin, the python path could be validated here.
        else:
            self.path = defaults.get_python_path(self.version)

    @property
    @abc.abstractmethod
    def is_managed(self) -> bool:
        """
        True if this Python is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have requirements installed without explicit permission from the user.
        """


@dataclasses.dataclass
class NativePythonConfig(PythonConfig):
    """Configuration for native Python."""

    @property
    def is_managed(self) -> bool:
        """
        True if this Python is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have requirements installed without explicit permission from the user.
        """
        return False


@dataclasses.dataclass
class VirtualPythonConfig(PythonConfig):
    """Configuration for Python in a virtual environment."""

    system_site_packages: t.Optional[bool] = None

    def apply_defaults(self, context: HostContext, defaults: PosixCompletionConfig) -> None:
        """Apply default settings."""
        super().apply_defaults(context, defaults)

        if self.system_site_packages is None:
            self.system_site_packages = False

    @property
    def is_managed(self) -> bool:
        """
        True if this Python is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have requirements installed without explicit permission from the user.
        """
        return True


@dataclasses.dataclass
class PosixConfig(HostConfig, metaclass=abc.ABCMeta):
    """Base class for POSIX host configuration."""

    python: t.Optional[PythonConfig] = None

    @property
    @abc.abstractmethod
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""

    @abc.abstractmethod
    def get_defaults(self, context: HostContext) -> PosixCompletionConfig:
        """Return the default settings."""

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, PosixCompletionConfig)

        super().apply_defaults(context, defaults)

        self.python = self.python or NativePythonConfig()
        self.python.apply_defaults(context, defaults)


@dataclasses.dataclass
class ControllerHostConfig(PosixConfig, metaclass=abc.ABCMeta):
    """Base class for host configurations which support the controller."""

    @abc.abstractmethod
    def get_default_targets(self, context: HostContext) -> list[ControllerConfig]:
        """Return the default targets for this host config."""


@dataclasses.dataclass
class RemoteConfig(HostConfig, metaclass=abc.ABCMeta):
    """Base class for remote host configuration."""

    name: t.Optional[str] = None
    provider: t.Optional[str] = None
    arch: t.Optional[str] = None

    @property
    def platform(self) -> str:
        """The name of the platform."""
        return self.name.partition('/')[0]

    @property
    def version(self) -> str:
        """The version of the platform."""
        return self.name.partition('/')[2]

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, RemoteCompletionConfig)

        super().apply_defaults(context, defaults)

        if self.provider == 'default':
            self.provider = None

        self.provider = self.provider or defaults.provider or 'aws'
        self.arch = self.arch or defaults.arch or Architecture.X86_64

    @property
    def is_managed(self) -> bool:
        """
        True if this host is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have destructive operations performed without explicit permission from the user.
        """
        return True


@dataclasses.dataclass
class PosixSshConfig(PosixConfig):
    """Configuration for a POSIX SSH host."""

    user: t.Optional[str] = None
    host: t.Optional[str] = None
    port: t.Optional[int] = None

    def get_defaults(self, context: HostContext) -> PosixSshCompletionConfig:
        """Return the default settings."""
        return PosixSshCompletionConfig(
            user=self.user,
            host=self.host,
        )

    @property
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""
        return self.user == 'root'


@dataclasses.dataclass
class InventoryConfig(HostConfig):
    """Configuration using inventory."""

    path: t.Optional[str] = None

    def get_defaults(self, context: HostContext) -> InventoryCompletionConfig:
        """Return the default settings."""
        return InventoryCompletionConfig()

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, InventoryCompletionConfig)


@dataclasses.dataclass
class DockerConfig(ControllerHostConfig, PosixConfig):
    """Configuration for a docker host."""

    name: t.Optional[str] = None
    image: t.Optional[str] = None
    memory: t.Optional[int] = None
    privileged: t.Optional[bool] = None
    seccomp: t.Optional[str] = None
    cgroup: t.Optional[CGroupVersion] = None
    audit: t.Optional[AuditMode] = None

    def get_defaults(self, context: HostContext) -> DockerCompletionConfig:
        """Return the default settings."""
        return filter_completion(docker_completion()).get(self.name) or DockerCompletionConfig(
            name=self.name,
            image=self.name,
            placeholder=True,
        )

    def get_default_targets(self, context: HostContext) -> list[ControllerConfig]:
        """Return the default targets for this host config."""
        if self.name in filter_completion(docker_completion()):
            defaults = self.get_defaults(context)
            pythons = {version: defaults.get_python_path(version) for version in defaults.supported_pythons}
        else:
            pythons = {context.controller_config.python.version: context.controller_config.python.path}

        return [ControllerConfig(python=NativePythonConfig(version=version, path=path)) for version, path in pythons.items()]

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, DockerCompletionConfig)

        super().apply_defaults(context, defaults)

        self.name = defaults.name
        self.image = defaults.image

        if self.seccomp is None:
            self.seccomp = defaults.seccomp

        if self.cgroup is None:
            self.cgroup = defaults.cgroup_enum

        if self.audit is None:
            self.audit = defaults.audit_enum

        if self.privileged is None:
            self.privileged = False

    @property
    def is_managed(self) -> bool:
        """
        True if this host is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have destructive operations performed without explicit permission from the user.
        """
        return True

    @property
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""
        return True


@dataclasses.dataclass
class PosixRemoteConfig(RemoteConfig, ControllerHostConfig, PosixConfig):
    """Configuration for a POSIX remote host."""

    become: t.Optional[str] = None

    def get_defaults(self, context: HostContext) -> PosixRemoteCompletionConfig:
        """Return the default settings."""
        # pylint: disable=unexpected-keyword-arg  # see: https://github.com/PyCQA/pylint/issues/7434
        return filter_completion(remote_completion()).get(self.name) or remote_completion().get(self.platform) or PosixRemoteCompletionConfig(
            name=self.name,
            placeholder=True,
        )

    def get_default_targets(self, context: HostContext) -> list[ControllerConfig]:
        """Return the default targets for this host config."""
        if self.name in filter_completion(remote_completion()):
            defaults = self.get_defaults(context)
            pythons = {version: defaults.get_python_path(version) for version in defaults.supported_pythons}
        else:
            pythons = {context.controller_config.python.version: context.controller_config.python.path}

        return [ControllerConfig(python=NativePythonConfig(version=version, path=path)) for version, path in pythons.items()]

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, PosixRemoteCompletionConfig)

        super().apply_defaults(context, defaults)

        self.become = self.become or defaults.become

    @property
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""
        return True


@dataclasses.dataclass
class WindowsConfig(HostConfig, metaclass=abc.ABCMeta):
    """Base class for Windows host configuration."""


@dataclasses.dataclass
class WindowsRemoteConfig(RemoteConfig, WindowsConfig):
    """Configuration for a remote Windows host."""

    def get_defaults(self, context: HostContext) -> WindowsRemoteCompletionConfig:
        """Return the default settings."""
        return filter_completion(windows_completion()).get(self.name) or windows_completion().get(self.platform)


@dataclasses.dataclass
class WindowsInventoryConfig(InventoryConfig, WindowsConfig):
    """Configuration for Windows hosts using inventory."""


@dataclasses.dataclass
class NetworkConfig(HostConfig, metaclass=abc.ABCMeta):
    """Base class for network host configuration."""


@dataclasses.dataclass
class NetworkRemoteConfig(RemoteConfig, NetworkConfig):
    """Configuration for a remote network host."""

    collection: t.Optional[str] = None
    connection: t.Optional[str] = None

    def get_defaults(self, context: HostContext) -> NetworkRemoteCompletionConfig:
        """Return the default settings."""
        return filter_completion(network_completion()).get(self.name) or NetworkRemoteCompletionConfig(
            name=self.name,
            placeholder=True,
        )

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, NetworkRemoteCompletionConfig)

        super().apply_defaults(context, defaults)

        self.collection = self.collection or defaults.collection
        self.connection = self.connection or defaults.connection


@dataclasses.dataclass
class NetworkInventoryConfig(InventoryConfig, NetworkConfig):
    """Configuration for network hosts using inventory."""


@dataclasses.dataclass
class OriginConfig(ControllerHostConfig, PosixConfig):
    """Configuration for the origin host."""

    def get_defaults(self, context: HostContext) -> OriginCompletionConfig:
        """Return the default settings."""
        return OriginCompletionConfig()

    def get_default_targets(self, context: HostContext) -> list[ControllerConfig]:
        """Return the default targets for this host config."""
        return [ControllerConfig(python=NativePythonConfig(version=version, path=path)) for version, path in get_available_python_versions().items()]

    @property
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""
        return os.getuid() == 0


@dataclasses.dataclass
class ControllerConfig(PosixConfig):
    """Configuration for the controller host."""

    controller: t.Optional[PosixConfig] = None

    def get_defaults(self, context: HostContext) -> PosixCompletionConfig:
        """Return the default settings."""
        return context.controller_config.get_defaults(context)

    def apply_defaults(self, context: HostContext, defaults: CompletionConfig) -> None:
        """Apply default settings."""
        assert isinstance(defaults, PosixCompletionConfig)

        self.controller = context.controller_config

        if not self.python and not defaults.supported_pythons:
            # The user did not specify a target Python and supported Pythons are unknown, so use the controller Python specified by the user instead.
            self.python = context.controller_config.python

        super().apply_defaults(context, defaults)

    @property
    def is_managed(self) -> bool:
        """
        True if the host is a managed instance, otherwise False.
        Managed instances are used exclusively by ansible-test and can safely have destructive operations performed without explicit permission from the user.
        """
        return self.controller.is_managed

    @property
    def have_root(self) -> bool:
        """True if root is available, otherwise False."""
        return self.controller.have_root


class FallbackReason(enum.Enum):
    """Reason fallback was performed."""

    ENVIRONMENT = enum.auto()
    PYTHON = enum.auto()


@dataclasses.dataclass(frozen=True)
class FallbackDetail:
    """Details about controller fallback behavior."""

    reason: FallbackReason
    message: str


@dataclasses.dataclass(frozen=True)
class HostSettings:
    """Host settings for the controller and targets."""

    controller: ControllerHostConfig
    targets: list[HostConfig]
    skipped_python_versions: list[str]
    filtered_args: list[str]
    controller_fallback: t.Optional[FallbackDetail]

    def serialize(self, path: str) -> None:
        """Serialize the host settings to the given path."""
        with open_binary_file(path, 'wb') as settings_file:
            pickle.dump(self, settings_file)

    @staticmethod
    def deserialize(path: str) -> HostSettings:
        """Deserialize host settings from the path."""
        with open_binary_file(path) as settings_file:
            return pickle.load(settings_file)

    def apply_defaults(self) -> None:
        """Apply defaults to the host settings."""
        context = HostContext(controller_config=None)
        self.controller.apply_defaults(context, self.controller.get_defaults(context))

        for target in self.targets:
            context = HostContext(controller_config=self.controller)
            target.apply_defaults(context, target.get_defaults(context))
