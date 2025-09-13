"""Code coverage support for integration tests."""

from __future__ import annotations

import abc
import json
import os
import shutil
import tempfile
import typing as t
import zipfile

from ...io import (
    write_text_file,
)

from ...ansible_util import (
    run_playbook,
)

from ...config import (
    IntegrationConfig,
)

from ...util import (
    COVERAGE_CONFIG_NAME,
    MODE_DIRECTORY,
    MODE_DIRECTORY_WRITE,
    MODE_FILE,
    SubprocessError,
    cache,
    display,
    generate_name,
    get_generic_type,
    get_type_map,
    remove_tree,
    sanitize_host_name,
    verified_chmod,
)

from ...util_common import (
    ResultType,
)

from ...coverage_util import (
    generate_coverage_config,
    get_coverage_platform,
)

from ...host_configs import (
    HostConfig,
    PosixConfig,
    WindowsConfig,
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from ...data import (
    data_context,
)

from ...host_profiles import (
    ControllerProfile,
    HostProfile,
    PosixProfile,
    SshTargetHostProfile,
)

from ...provisioning import (
    HostState,
)

from ...connections import (
    LocalConnection,
)

from ...inventory import (
    create_windows_inventory,
    create_posix_inventory,
)


class CoverageHandler[THostConfig: HostConfig](metaclass=abc.ABCMeta):
    """Base class for configuring hosts for integration test code coverage."""

    def __init__(self, args: IntegrationConfig, host_state: HostState, inventory_path: str) -> None:
        self.args = args
        self.host_state = host_state
        self.inventory_path = inventory_path
        self.profiles = self.get_profiles()

    def get_profiles(self) -> list[HostProfile]:
        """Return a list of profiles relevant for this handler."""
        profile_type = get_generic_type(type(self), HostConfig)
        profiles = [profile for profile in self.host_state.target_profiles if isinstance(profile.config, profile_type)]

        return profiles

    @property
    @abc.abstractmethod
    def is_active(self) -> bool:
        """True if the handler should be used, otherwise False."""

    @abc.abstractmethod
    def setup(self) -> None:
        """Perform setup for code coverage."""

    @abc.abstractmethod
    def teardown(self) -> None:
        """Perform teardown for code coverage."""

    @abc.abstractmethod
    def create_inventory(self) -> None:
        """Create inventory, if needed."""

    @abc.abstractmethod
    def get_environment(self, target_name: str, aliases: tuple[str, ...]) -> dict[str, str]:
        """Return a dictionary of environment variables for running tests with code coverage."""

    def run_playbook(self, playbook: str, variables: dict[str, str]) -> None:
        """Run the specified playbook using the current inventory."""
        self.create_inventory()
        run_playbook(self.args, self.inventory_path, playbook, capture=False, variables=variables)


class PosixCoverageHandler(CoverageHandler[PosixConfig]):
    """Configure integration test code coverage for POSIX hosts."""

    def __init__(self, args: IntegrationConfig, host_state: HostState, inventory_path: str) -> None:
        super().__init__(args, host_state, inventory_path)

        # Common temporary directory used on all POSIX hosts that will be created world writeable.
        self.common_temp_path = f'/tmp/ansible-test-{generate_name()}'

    def get_profiles(self) -> list[HostProfile]:
        """Return a list of profiles relevant for this handler."""
        profiles = super().get_profiles()
        profiles = [profile for profile in profiles if not isinstance(profile, ControllerProfile) or
                    profile.python.path != self.host_state.controller_profile.python.path]

        return profiles

    @property
    def is_active(self) -> bool:
        """True if the handler should be used, otherwise False."""
        return True

    @property
    def target_profile(self) -> t.Optional[PosixProfile]:
        """The POSIX target profile, if it uses a different Python interpreter than the controller, otherwise None."""
        return t.cast(PosixProfile, self.profiles[0]) if self.profiles else None

    def setup(self) -> None:
        """Perform setup for code coverage."""
        self.setup_controller()
        self.setup_target()

    def teardown(self) -> None:
        """Perform teardown for code coverage."""
        self.teardown_controller()
        self.teardown_target()

    def setup_controller(self) -> None:
        """Perform setup for code coverage on the controller."""
        coverage_config_path = os.path.join(self.common_temp_path, COVERAGE_CONFIG_NAME)
        coverage_output_path = os.path.join(self.common_temp_path, ResultType.COVERAGE.name)

        coverage_config = generate_coverage_config()

        write_text_file(coverage_config_path, coverage_config, create_directories=True)

        verified_chmod(coverage_config_path, MODE_FILE)
        os.mkdir(coverage_output_path)
        verified_chmod(coverage_output_path, MODE_DIRECTORY_WRITE)

    def setup_target(self) -> None:
        """Perform setup for code coverage on the target."""
        if not self.target_profile:
            return

        if isinstance(self.target_profile, ControllerProfile):
            return

        self.run_playbook('posix_coverage_setup.yml', self.get_playbook_variables())

    def teardown_controller(self) -> None:
        """Perform teardown for code coverage on the controller."""
        coverage_temp_path = os.path.join(self.common_temp_path, ResultType.COVERAGE.name)
        platform = get_coverage_platform(self.args.controller)

        for filename in os.listdir(coverage_temp_path):
            shutil.copyfile(os.path.join(coverage_temp_path, filename), os.path.join(ResultType.COVERAGE.path, update_coverage_filename(filename, platform)))

        remove_tree(self.common_temp_path)

    def teardown_target(self) -> None:
        """Perform teardown for code coverage on the target."""
        if not self.target_profile:
            return

        if isinstance(self.target_profile, ControllerProfile):
            return

        profile = t.cast(SshTargetHostProfile, self.target_profile)
        platform = get_coverage_platform(profile.config)
        con = profile.get_controller_target_connections()[0]

        with tempfile.NamedTemporaryFile(prefix='ansible-test-coverage-', suffix='.tgz') as coverage_tgz:
            try:
                con.create_archive(chdir=self.common_temp_path, name=ResultType.COVERAGE.name, dst=coverage_tgz)
            except SubprocessError as ex:
                display.warning(f'Failed to download coverage results: {ex}')
            else:
                coverage_tgz.seek(0)

                with tempfile.TemporaryDirectory() as temp_dir:
                    local_con = LocalConnection(self.args)
                    local_con.extract_archive(chdir=temp_dir, src=coverage_tgz)

                    base_dir = os.path.join(temp_dir, ResultType.COVERAGE.name)

                    for filename in os.listdir(base_dir):
                        shutil.copyfile(os.path.join(base_dir, filename), os.path.join(ResultType.COVERAGE.path, update_coverage_filename(filename, platform)))

        self.run_playbook('posix_coverage_teardown.yml', self.get_playbook_variables())

    def get_environment(self, target_name: str, aliases: tuple[str, ...]) -> dict[str, str]:
        """Return a dictionary of environment variables for running tests with code coverage."""

        # Enable code coverage collection on Ansible modules (both local and remote).
        # Used by the AnsiballZ wrapper generator in lib/ansible/executor/module_common.py to support code coverage.
        config_file = os.path.join(self.common_temp_path, COVERAGE_CONFIG_NAME)

        # Include the command, target and platform marker so the remote host can create a filename with that info.
        # The generated AnsiballZ wrapper is responsible for adding '=python-{X.Y}=coverage.{hostname}.{pid}.{id}'
        coverage_file = os.path.join(self.common_temp_path, ResultType.COVERAGE.name, '='.join((self.args.command, target_name, 'platform')))

        if self.args.coverage_check:
            # cause the 'coverage' module to be found, but not imported or enabled
            coverage_file = ''

        coverage_options = dict(
            config=config_file,
            output=coverage_file,
        )

        variables = dict(
            _ANSIBLE_ANSIBALLZ_COVERAGE_CONFIG=json.dumps(coverage_options),
        )

        return variables

    def create_inventory(self) -> None:
        """Create inventory."""
        create_posix_inventory(self.args, self.inventory_path, self.host_state.target_profiles)

    def get_playbook_variables(self) -> dict[str, str]:
        """Return a dictionary of variables for setup and teardown of POSIX coverage."""
        return dict(
            common_temp_dir=self.common_temp_path,
            coverage_config=generate_coverage_config(),
            coverage_config_path=os.path.join(self.common_temp_path, COVERAGE_CONFIG_NAME),
            coverage_output_path=os.path.join(self.common_temp_path, ResultType.COVERAGE.name),
            mode_directory=f'{MODE_DIRECTORY:04o}',
            mode_directory_write=f'{MODE_DIRECTORY_WRITE:04o}',
            mode_file=f'{MODE_FILE:04o}',
        )


class WindowsCoverageHandler(CoverageHandler[WindowsConfig]):
    """Configure integration test code coverage for Windows hosts."""

    def __init__(self, args: IntegrationConfig, host_state: HostState, inventory_path: str) -> None:
        super().__init__(args, host_state, inventory_path)

        # Common temporary directory used on all Windows hosts that will be created writable by everyone.
        self.remote_temp_path = f'C:\\ansible_test_coverage_{generate_name()}'

    @property
    def is_active(self) -> bool:
        """True if the handler should be used, otherwise False."""
        return bool(self.profiles) and not self.args.coverage_check

    def setup(self) -> None:
        """Perform setup for code coverage."""
        self.run_playbook('windows_coverage_setup.yml', self.get_playbook_variables())

    def teardown(self) -> None:
        """Perform teardown for code coverage."""
        with tempfile.TemporaryDirectory() as local_temp_path:
            variables = self.get_playbook_variables()
            variables.update(
                local_temp_path=local_temp_path,
            )

            self.run_playbook('windows_coverage_teardown.yml', variables)

            for filename in os.listdir(local_temp_path):
                if all(isinstance(profile.config, WindowsRemoteConfig) for profile in self.profiles):
                    prefix = 'remote'
                elif all(isinstance(profile.config, WindowsInventoryConfig) for profile in self.profiles):
                    prefix = 'inventory'
                else:
                    raise NotImplementedError()

                platform = f'{prefix}-{sanitize_host_name(os.path.splitext(filename)[0])}'

                with zipfile.ZipFile(os.path.join(local_temp_path, filename)) as coverage_zip:
                    for item in coverage_zip.infolist():
                        if item.is_dir():
                            raise Exception(f'Unexpected directory in zip file: {item.filename}')

                        item.filename = update_coverage_filename(item.filename, platform)

                        coverage_zip.extract(item, ResultType.COVERAGE.path)

    def get_environment(self, target_name: str, aliases: tuple[str, ...]) -> dict[str, str]:
        """Return a dictionary of environment variables for running tests with code coverage."""

        # Include the command, target and platform marker so the remote host can create a filename with that info.
        # The remote is responsible for adding '={language-version}=coverage.{hostname}.{pid}.{id}'
        coverage_name = '='.join((self.args.command, target_name, 'platform'))

        variables = dict(
            _ANSIBLE_COVERAGE_REMOTE_OUTPUT=os.path.join(self.remote_temp_path, coverage_name),
            _ANSIBLE_COVERAGE_REMOTE_PATH_FILTER=os.path.join(data_context().content.root, '*'),
        )

        return variables

    def create_inventory(self) -> None:
        """Create inventory."""
        create_windows_inventory(self.args, self.inventory_path, self.host_state.target_profiles)

    def get_playbook_variables(self) -> dict[str, str]:
        """Return a dictionary of variables for setup and teardown of Windows coverage."""
        return dict(
            remote_temp_path=self.remote_temp_path,
        )


class CoverageManager:
    """Manager for code coverage configuration and state."""

    def __init__(self, args: IntegrationConfig, host_state: HostState, inventory_path: str) -> None:
        self.args = args
        self.host_state = host_state
        self.inventory_path = inventory_path

        if self.args.coverage:
            handler_types = set(get_handler_type(type(profile.config)) for profile in host_state.profiles)
            handler_types.discard(None)
        else:
            handler_types = set()

        handlers = [handler_type(args=args, host_state=host_state, inventory_path=inventory_path) for handler_type in handler_types]

        self.handlers = [handler for handler in handlers if handler.is_active]

    def setup(self) -> None:
        """Perform setup for code coverage."""
        if not self.args.coverage:
            return

        for handler in self.handlers:
            handler.setup()

    def teardown(self) -> None:
        """Perform teardown for code coverage."""
        if not self.args.coverage:
            return

        for handler in self.handlers:
            handler.teardown()

    def get_environment(self, target_name: str, aliases: tuple[str, ...]) -> dict[str, str]:
        """Return a dictionary of environment variables for running tests with code coverage."""
        if not self.args.coverage or 'non_local/' in aliases:
            return {}

        env = {}

        for handler in self.handlers:
            env.update(handler.get_environment(target_name, aliases))

        return env


@cache
def get_config_handler_type_map() -> dict[t.Type[HostConfig], t.Type[CoverageHandler]]:
    """Create and return a mapping of HostConfig types to CoverageHandler types."""
    return get_type_map(CoverageHandler, HostConfig)


def get_handler_type(config_type: t.Type[HostConfig]) -> t.Optional[t.Type[CoverageHandler]]:
    """Return the coverage handler type associated with the given host config type if found, otherwise return None."""
    queue = [config_type]
    type_map = get_config_handler_type_map()

    while queue:
        config_type = queue.pop(0)
        handler_type = type_map.get(config_type)

        if handler_type:
            return handler_type

        queue.extend(config_type.__bases__)

    return None


def update_coverage_filename(original_filename: str, platform: str) -> str:
    """Validate the given filename and insert the specified platform, then return the result."""
    parts = original_filename.split('=')

    if original_filename != os.path.basename(original_filename) or len(parts) != 5 or parts[2] != 'platform':
        raise Exception(f'Unexpected coverage filename: {original_filename}')

    parts[2] = platform

    updated_filename = '='.join(parts)

    display.info(f'Coverage file for platform "{platform}": {original_filename} -> {updated_filename}', verbosity=3)

    return updated_filename
