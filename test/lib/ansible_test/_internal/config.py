"""Configuration classes."""
from __future__ import annotations

import enum
import os
import sys
import typing as t

from .util import (
    display,
    verify_sys_executable,
    version_to_str,
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


class ParsedRemote:
    """A parsed version of a "remote" string."""
    def __init__(self, arch, platform, version):  # type: (t.Optional[str], str, str) -> None
        self.arch = arch
        self.platform = platform
        self.version = version

    @staticmethod
    def parse(value):  # type: (str) -> t.Optional['ParsedRemote']
        """Return a ParsedRemote from the given value or None if the syntax is invalid."""
        parts = value.split('/')

        if len(parts) == 2:
            arch = None
            platform, version = parts
        elif len(parts) == 3:
            arch, platform, version = parts
        else:
            return None

        return ParsedRemote(arch, platform, version)


class EnvironmentConfig(CommonConfig):
    """Configuration common to all commands which execute in an environment."""
    def __init__(self, args, command):  # type: (t.Any, str) -> None
        super().__init__(args, command)

        self.host_settings = args.host_settings  # type: HostSettings
        self.host_path = args.host_path  # type: t.Optional[str]
        self.containers = args.containers  # type: t.Optional[str]
        self.pypi_proxy = args.pypi_proxy  # type: bool
        self.pypi_endpoint = args.pypi_endpoint  # type: t.Optional[str]

        # Set by check_controller_python once HostState has been created by prepare_profiles.
        # This is here for convenience, to avoid needing to pass HostState to some functions which already have access to EnvironmentConfig.
        self.controller_python = None  # type: t.Optional[PythonConfig]
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
                or verify_sys_executable(self.controller.python.path)
            )

        self.docker_network = args.docker_network  # type: t.Optional[str]
        self.docker_terminate = args.docker_terminate  # type: t.Optional[TerminateMode]

        self.remote_endpoint = args.remote_endpoint  # type: t.Optional[str]
        self.remote_stage = args.remote_stage  # type: t.Optional[str]
        self.remote_terminate = args.remote_terminate  # type: t.Optional[TerminateMode]

        self.prime_containers = args.prime_containers  # type: bool

        self.requirements = args.requirements  # type: bool

        self.delegate_args = []  # type: t.List[str]

        def host_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """Add the host files to the payload file list."""
            config = self

            if config.host_path:
                settings_path = os.path.join(config.host_path, 'settings.dat')
                state_path = os.path.join(config.host_path, 'state.dat')

                files.append((os.path.abspath(settings_path), settings_path))
                files.append((os.path.abspath(state_path), state_path))

        data_context().register_payload_callback(host_callback)

        if args.docker_no_pull:
            display.warning('The --docker-no-pull option is deprecated and has no effect. It will be removed in a future version of ansible-test.')

        if args.no_pip_check:
            display.warning('The --no-pip-check option is deprecated and has no effect. It will be removed in a future version of ansible-test.')

    @property
    def controller(self):  # type: () -> ControllerHostConfig
        """Host configuration for the controller."""
        return self.host_settings.controller

    @property
    def targets(self):  # type: () -> t.List[HostConfig]
        """Host configuration for the targets."""
        return self.host_settings.targets

    def only_target(self, target_type):  # type: (t.Type[THostConfig]) -> THostConfig
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

    def only_targets(self, target_type):  # type: (t.Type[THostConfig]) -> t.List[THostConfig]
        """
        Return a list of target host configurations.
        Requires that there are one or more targets, all of the specified type.
        """
        if not self.targets:
            raise Exception('There must be one or more targets.')

        for target in self.targets:
            if not isinstance(target, target_type):
                raise Exception(f'Target is {type(target_type)} instead of {target_type}.')

        return self.targets

    @property
    def target_type(self):  # type: () -> t.Type[HostConfig]
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
    def __init__(self, args, command):  # type: (t.Any, str) -> None
        super().__init__(args, command)

        self.coverage = args.coverage  # type: bool
        self.coverage_check = args.coverage_check  # type: bool
        self.include = args.include or []  # type: t.List[str]
        self.exclude = args.exclude or []  # type: t.List[str]
        self.require = args.require or []  # type: t.List[str]

        self.changed = args.changed  # type: bool
        self.tracked = args.tracked  # type: bool
        self.untracked = args.untracked  # type: bool
        self.committed = args.committed  # type: bool
        self.staged = args.staged  # type: bool
        self.unstaged = args.unstaged  # type: bool
        self.changed_from = args.changed_from  # type: str
        self.changed_path = args.changed_path  # type: t.List[str]
        self.base_branch = args.base_branch  # type: str

        self.lint = getattr(args, 'lint', False)  # type: bool
        self.junit = getattr(args, 'junit', False)  # type: bool
        self.failure_ok = getattr(args, 'failure_ok', False)  # type: bool

        self.metadata = Metadata.from_file(args.metadata) if args.metadata else Metadata()
        self.metadata_path = None

        if self.coverage_check:
            self.coverage = True

        def metadata_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """Add the metadata file to the payload file list."""
            config = self

            if config.metadata_path:
                files.append((os.path.abspath(config.metadata_path), config.metadata_path))

        data_context().register_payload_callback(metadata_callback)


class ShellConfig(EnvironmentConfig):
    """Configuration for the shell command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'shell')

        self.raw = args.raw  # type: bool


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'sanity')

        self.test = args.test  # type: t.List[str]
        self.skip_test = args.skip_test  # type: t.List[str]
        self.list_tests = args.list_tests  # type: bool
        self.allow_disabled = args.allow_disabled  # type: bool
        self.enable_optional_errors = args.enable_optional_errors  # type: bool
        self.keep_git = args.keep_git  # type: bool
        self.prime_venvs = args.prime_venvs  # type: bool

        self.info_stderr = self.lint

        if self.keep_git:
            def git_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
                """Add files from the content root .git directory to the payload file list."""
                for dirpath, _dirnames, filenames in os.walk(os.path.join(data_context().content.root, '.git')):
                    paths = [os.path.join(dirpath, filename) for filename in filenames]
                    files.extend((path, os.path.relpath(path, data_context().content.root)) for path in paths)

            data_context().register_payload_callback(git_callback)


class IntegrationConfig(TestConfig):
    """Configuration for the integration command."""
    def __init__(self, args, command):  # type: (t.Any, str) -> None
        super().__init__(args, command)

        self.start_at = args.start_at  # type: str
        self.start_at_task = args.start_at_task  # type: str
        self.allow_destructive = args.allow_destructive  # type: bool
        self.allow_root = args.allow_root  # type: bool
        self.allow_disabled = args.allow_disabled  # type: bool
        self.allow_unstable = args.allow_unstable  # type: bool
        self.allow_unstable_changed = args.allow_unstable_changed  # type: bool
        self.allow_unsupported = args.allow_unsupported  # type: bool
        self.retry_on_error = args.retry_on_error  # type: bool
        self.continue_on_error = args.continue_on_error  # type: bool
        self.debug_strategy = args.debug_strategy  # type: bool
        self.changed_all_target = args.changed_all_target  # type: str
        self.changed_all_mode = args.changed_all_mode  # type: str
        self.list_targets = args.list_targets  # type: bool
        self.tags = args.tags
        self.skip_tags = args.skip_tags
        self.diff = args.diff
        self.no_temp_workdir = args.no_temp_workdir
        self.no_temp_unicode = args.no_temp_unicode

        if self.list_targets:
            self.explain = True
            self.info_stderr = True

    def get_ansible_config(self):  # type: () -> str
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
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'integration')


class WindowsIntegrationConfig(IntegrationConfig):
    """Configuration for the windows integration command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'windows-integration')


class NetworkIntegrationConfig(IntegrationConfig):
    """Configuration for the network integration command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'network-integration')

        self.testcase = args.testcase  # type: str


class UnitsConfig(TestConfig):
    """Configuration for the units command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super().__init__(args, 'units')

        self.collect_only = args.collect_only  # type: bool
        self.num_workers = args.num_workers  # type: int

        self.requirements_mode = getattr(args, 'requirements_mode', '')  # type: str

        if self.requirements_mode == 'only':
            self.requirements = True
        elif self.requirements_mode == 'skip':
            self.requirements = False
