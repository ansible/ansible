"""Configuration classes."""
from __future__ import annotations

import dataclasses
import enum
import os
import sys
import typing as t

from .util import (
    display,
    verify_sys_executable,
    version_to_str,
    type_guard,
)

from .util_common import (
    CommonConfig,
)

from .metadata import (
    Metadata,
)

from .data import (
    data_context,
)

from .host_configs import (
    ControllerConfig,
    ControllerHostConfig,
    HostConfig,
    HostSettings,
    OriginConfig,
    PythonConfig,
    VirtualPythonConfig,
)

THostConfig = t.TypeVar('THostConfig', bound=HostConfig)


class TerminateMode(enum.Enum):
    """When to terminate instances."""
    ALWAYS = enum.auto()
    NEVER = enum.auto()
    SUCCESS = enum.auto()

    def __str__(self):
        return self.name.lower()


@dataclasses.dataclass(frozen=True)
class ModulesConfig:
    """Configuration for modules."""
    python_requires: str
    python_versions: tuple[str, ...]
    controller_only: bool


@dataclasses.dataclass(frozen=True)
class ContentConfig:
    """Configuration for all content."""
    modules: ModulesConfig
    python_versions: tuple[str, ...]
    py2_support: bool


class EnvironmentConfig(CommonConfig):
    """Configuration common to all commands which execute in an environment."""
    def __init__(self, args: t.Any, command: str) -> None:
        super().__init__(args, command)

        self.host_settings: HostSettings = args.host_settings
        self.host_path: t.Optional[str] = args.host_path
        self.containers: t.Optional[str] = args.containers
        self.pypi_proxy: bool = args.pypi_proxy
        self.pypi_endpoint: t.Optional[str] = args.pypi_endpoint

        # Populated by content_config.get_content_config on the origin.
        # Serialized and passed to delegated instances to avoid parsing a second time.
        self.content_config: t.Optional[ContentConfig] = None

        # Set by check_controller_python once HostState has been created by prepare_profiles.
        # This is here for convenience, to avoid needing to pass HostState to some functions which already have access to EnvironmentConfig.
        self.controller_python: t.Optional[PythonConfig] = None
        """
        The Python interpreter used by the controller.
        Only available after delegation has been performed or skipped (if delegation is not required).
        """

        if self.host_path:
            self.delegate = False
        else:
            self.delegate = (
                not isinstance(self.controller, OriginConfig)
                or isinstance(self.controller.python, VirtualPythonConfig)
                or self.controller.python.version != version_to_str(sys.version_info[:2])
                or bool(verify_sys_executable(self.controller.python.path))
            )

        self.docker_network: t.Optional[str] = args.docker_network
        self.docker_terminate: t.Optional[TerminateMode] = args.docker_terminate

        self.remote_endpoint: t.Optional[str] = args.remote_endpoint
        self.remote_stage: t.Optional[str] = args.remote_stage
        self.remote_terminate: t.Optional[TerminateMode] = args.remote_terminate

        self.prime_containers: bool = args.prime_containers

        self.requirements: bool = args.requirements

        self.delegate_args: list[str] = []

        def host_callback(files: list[tuple[str, str]]) -> None:
            """Add the host files to the payload file list."""
            config = self

            if config.host_path:
                settings_path = os.path.join(config.host_path, 'settings.dat')
                state_path = os.path.join(config.host_path, 'state.dat')
                config_path = os.path.join(config.host_path, 'config.dat')

                files.append((os.path.abspath(settings_path), settings_path))
                files.append((os.path.abspath(state_path), state_path))
                files.append((os.path.abspath(config_path), config_path))

        data_context().register_payload_callback(host_callback)

        if args.docker_no_pull:
            display.warning('The --docker-no-pull option is deprecated and has no effect. It will be removed in a future version of ansible-test.')

        if args.no_pip_check:
            display.warning('The --no-pip-check option is deprecated and has no effect. It will be removed in a future version of ansible-test.')

    @property
    def controller(self) -> ControllerHostConfig:
        """Host configuration for the controller."""
        return self.host_settings.controller

    @property
    def targets(self) -> list[HostConfig]:
        """Host configuration for the targets."""
        return self.host_settings.targets

    def only_target(self, target_type: t.Type[THostConfig]) -> THostConfig:
        """
        Return the host configuration for the target.
        Requires that there is exactly one target of the specified type.
        """
        targets = list(self.targets)

        if len(targets) != 1:
            raise Exception('There must be exactly one target.')

        target = targets.pop()

        if not isinstance(target, target_type):
            raise Exception(f'Target is {type(target_type)} instead of {target_type}.')

        return target

    def only_targets(self, target_type: t.Type[THostConfig]) -> list[THostConfig]:
        """
        Return a list of target host configurations.
        Requires that there are one or more targets, all the specified type.
        """
        if not self.targets:
            raise Exception('There must be one or more targets.')

        assert type_guard(self.targets, target_type)

        return t.cast(list[THostConfig], self.targets)

    @property
    def target_type(self) -> t.Type[HostConfig]:
        """
        The true type of the target(s).
        If the target is the controller, the controller type is returned.
        Requires at least one target, and all targets must be of the same type.
        """
        target_types = set(type(target) for target in self.targets)

        if len(target_types) != 1:
            raise Exception('There must be one or more targets, all of the same type.')

        target_type = target_types.pop()

        if issubclass(target_type, ControllerConfig):
            target_type = type(self.controller)

        return target_type


class TestConfig(EnvironmentConfig):
    """Configuration common to all test commands."""
    def __init__(self, args: t.Any, command: str) -> None:
        super().__init__(args, command)

        self.coverage: bool = args.coverage
        self.coverage_check: bool = args.coverage_check
        self.include: list[str] = args.include or []
        self.exclude: list[str] = args.exclude or []
        self.require: list[str] = args.require or []

        self.changed: bool = args.changed
        self.tracked: bool = args.tracked
        self.untracked: bool = args.untracked
        self.committed: bool = args.committed
        self.staged: bool = args.staged
        self.unstaged: bool = args.unstaged
        self.changed_from: str = args.changed_from
        self.changed_path: list[str] = args.changed_path
        self.base_branch: str = args.base_branch

        self.lint: bool = getattr(args, 'lint', False)
        self.junit: bool = getattr(args, 'junit', False)
        self.failure_ok: bool = getattr(args, 'failure_ok', False)

        self.metadata = Metadata.from_file(args.metadata) if args.metadata else Metadata()
        self.metadata_path: t.Optional[str] = None

        if self.coverage_check:
            self.coverage = True

        def metadata_callback(files: list[tuple[str, str]]) -> None:
            """Add the metadata file to the payload file list."""
            config = self

            if config.metadata_path:
                files.append((os.path.abspath(config.metadata_path), config.metadata_path))

        data_context().register_payload_callback(metadata_callback)


class ShellConfig(EnvironmentConfig):
    """Configuration for the shell command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'shell')

        self.cmd: list[str] = args.cmd
        self.raw: bool = args.raw
        self.check_layout = self.delegate  # allow shell to be used without a valid layout as long as no delegation is required
        self.interactive = sys.stdin.isatty() and not args.cmd  # delegation should only be interactive when stdin is a TTY and no command was given
        self.export: t.Optional[str] = args.export
        self.display_stderr = True


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'sanity')

        self.test: list[str] = args.test
        self.skip_test: list[str] = args.skip_test
        self.list_tests: bool = args.list_tests
        self.allow_disabled: bool = args.allow_disabled
        self.enable_optional_errors: bool = args.enable_optional_errors
        self.keep_git: bool = args.keep_git
        self.prime_venvs: bool = args.prime_venvs

        self.display_stderr = self.lint or self.list_tests

        if self.keep_git:
            def git_callback(files: list[tuple[str, str]]) -> None:
                """Add files from the content root .git directory to the payload file list."""
                for dirpath, _dirnames, filenames in os.walk(os.path.join(data_context().content.root, '.git')):
                    paths = [os.path.join(dirpath, filename) for filename in filenames]
                    files.extend((path, os.path.relpath(path, data_context().content.root)) for path in paths)

            data_context().register_payload_callback(git_callback)


class IntegrationConfig(TestConfig):
    """Configuration for the integration command."""
    def __init__(self, args: t.Any, command: str) -> None:
        super().__init__(args, command)

        self.start_at: str = args.start_at
        self.start_at_task: str = args.start_at_task
        self.allow_destructive: bool = args.allow_destructive
        self.allow_root: bool = args.allow_root
        self.allow_disabled: bool = args.allow_disabled
        self.allow_unstable: bool = args.allow_unstable
        self.allow_unstable_changed: bool = args.allow_unstable_changed
        self.allow_unsupported: bool = args.allow_unsupported
        self.retry_on_error: bool = args.retry_on_error
        self.continue_on_error: bool = args.continue_on_error
        self.debug_strategy: bool = args.debug_strategy
        self.changed_all_target: str = args.changed_all_target
        self.changed_all_mode: str = args.changed_all_mode
        self.list_targets: bool = args.list_targets
        self.tags = args.tags
        self.skip_tags = args.skip_tags
        self.diff = args.diff
        self.no_temp_workdir: bool = args.no_temp_workdir
        self.no_temp_unicode: bool = args.no_temp_unicode

        if self.list_targets:
            self.explain = True
            self.display_stderr = True

    def get_ansible_config(self) -> str:
        """Return the path to the Ansible config for the given config."""
        ansible_config_relative_path = os.path.join(data_context().content.integration_path, '%s.cfg' % self.command)
        ansible_config_path = os.path.join(data_context().content.root, ansible_config_relative_path)

        if not os.path.exists(ansible_config_path):
            # use the default empty configuration unless one has been provided
            ansible_config_path = super().get_ansible_config()

        return ansible_config_path


TIntegrationConfig = t.TypeVar('TIntegrationConfig', bound=IntegrationConfig)


class PosixIntegrationConfig(IntegrationConfig):
    """Configuration for the posix integration command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'integration')


class WindowsIntegrationConfig(IntegrationConfig):
    """Configuration for the windows integration command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'windows-integration')


class NetworkIntegrationConfig(IntegrationConfig):
    """Configuration for the network integration command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'network-integration')

        self.testcase: str = args.testcase


class UnitsConfig(TestConfig):
    """Configuration for the units command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'units')

        self.collect_only: bool = args.collect_only
        self.num_workers: int = args.num_workers

        self.requirements_mode: str = getattr(args, 'requirements_mode', '')

        if self.requirements_mode == 'only':
            self.requirements = True
        elif self.requirements_mode == 'skip':
            self.requirements = False
