"""Profiles to represent individual test hosts or a user-provided inventory file."""
from __future__ import annotations

import abc
import dataclasses
import os
import tempfile
import time
import typing as t

from .io import (
    write_text_file,
)

from .config import (
    CommonConfig,
    EnvironmentConfig,
    IntegrationConfig,
    TerminateMode,
)

from .host_configs import (
    ControllerConfig,
    ControllerHostConfig,
    DockerConfig,
    HostConfig,
    NetworkInventoryConfig,
    NetworkRemoteConfig,
    OriginConfig,
    PosixConfig,
    PosixRemoteConfig,
    PosixSshConfig,
    PythonConfig,
    RemoteConfig,
    VirtualPythonConfig,
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from .core_ci import (
    AnsibleCoreCI,
    SshKey,
    VmResource,
)

from .util import (
    ApplicationError,
    SubprocessError,
    cache,
    display,
    get_type_map,
    sanitize_host_name,
    sorted_versions,
    InternalError,
)

from .util_common import (
    intercept_python,
)

from .docker_util import (
    docker_exec,
    docker_rm,
    get_docker_hostname,
)

from .bootstrap import (
    BootstrapDocker,
    BootstrapRemote,
)

from .venv import (
    get_virtual_python,
)

from .ssh import (
    SshConnectionDetail,
)

from .ansible_util import (
    ansible_environment,
    get_hosts,
    parse_inventory,
)

from .containers import (
    CleanupMode,
    HostType,
    get_container_database,
    run_support_container,
)

from .connections import (
    Connection,
    DockerConnection,
    LocalConnection,
    SshConnection,
)

from .become import (
    Become,
    SUPPORTED_BECOME_METHODS,
    Sudo,
)

TControllerHostConfig = t.TypeVar('TControllerHostConfig', bound=ControllerHostConfig)
THostConfig = t.TypeVar('THostConfig', bound=HostConfig)
TPosixConfig = t.TypeVar('TPosixConfig', bound=PosixConfig)
TRemoteConfig = t.TypeVar('TRemoteConfig', bound=RemoteConfig)


@dataclasses.dataclass(frozen=True)
class Inventory:
    """Simple representation of an Ansible inventory."""
    host_groups: dict[str, dict[str, dict[str, t.Union[str, int]]]]
    extra_groups: t.Optional[dict[str, list[str]]] = None

    @staticmethod
    def create_single_host(name: str, variables: dict[str, t.Union[str, int]]) -> Inventory:
        """Return an inventory instance created from the given hostname and variables."""
        return Inventory(host_groups=dict(all={name: variables}))

    def write(self, args: CommonConfig, path: str) -> None:
        """Write the given inventory to the specified path on disk."""

        # NOTE: Switching the inventory generation to write JSON would be nice, but is currently not possible due to the use of hard-coded inventory filenames.
        #       The name `inventory` works for the POSIX integration tests, but `inventory.winrm` and `inventory.networking` will only parse in INI format.
        #       If tests are updated to use the `INVENTORY_PATH` environment variable, then this could be changed.
        #       Also, some tests detect the test type by inspecting the suffix on the inventory filename, which would break if it were changed.

        inventory_text = ''

        for group, hosts in self.host_groups.items():
            inventory_text += f'[{group}]\n'

            for host, variables in hosts.items():
                kvp = ' '.join(f'{key}="{value}"' for key, value in variables.items())
                inventory_text += f'{host} {kvp}\n'

            inventory_text += '\n'

        for group, children in (self.extra_groups or {}).items():
            inventory_text += f'[{group}]\n'

            for child in children:
                inventory_text += f'{child}\n'

            inventory_text += '\n'

        inventory_text = inventory_text.strip()

        if not args.explain:
            write_text_file(path, inventory_text + '\n')

        display.info(f'>>> Inventory\n{inventory_text}', verbosity=3)


class HostProfile(t.Generic[THostConfig], metaclass=abc.ABCMeta):
    """Base class for host profiles."""
    def __init__(self,
                 *,
                 args: EnvironmentConfig,
                 config: THostConfig,
                 targets: t.Optional[list[HostConfig]],
                 ) -> None:
        self.args = args
        self.config = config
        self.controller = bool(targets)
        self.targets = targets or []

        self.state: dict[str, t.Any] = {}
        """State that must be persisted across delegation."""
        self.cache: dict[str, t.Any] = {}
        """Cache that must not be persisted across delegation."""

    def provision(self) -> None:
        """Provision the host before delegation."""

    def setup(self) -> None:
        """Perform out-of-band setup before delegation."""

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""

    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""

    def configure(self) -> None:
        """Perform in-band configuration. Executed before delegation for the controller and after delegation for targets."""

    def __getstate__(self):
        return {key: value for key, value in self.__dict__.items() if key not in ('args', 'cache')}

    def __setstate__(self, state):
        self.__dict__.update(state)

        # args will be populated after the instances are restored
        self.cache = {}


class PosixProfile(HostProfile[TPosixConfig], metaclass=abc.ABCMeta):
    """Base class for POSIX host profiles."""
    @property
    def python(self) -> PythonConfig:
        """
        The Python to use for this profile.
        If it is a virtual python, it will be created the first time it is requested.
        """
        python = self.state.get('python')

        if not python:
            python = self.config.python

            if isinstance(python, VirtualPythonConfig):
                python = get_virtual_python(self.args, python)

            self.state['python'] = python

        return python


class ControllerHostProfile(PosixProfile[TControllerHostConfig], metaclass=abc.ABCMeta):
    """Base class for profiles usable as a controller."""
    @abc.abstractmethod
    def get_origin_controller_connection(self) -> Connection:
        """Return a connection for accessing the host as a controller from the origin."""

    @abc.abstractmethod
    def get_working_directory(self) -> str:
        """Return the working directory for the host."""


class SshTargetHostProfile(HostProfile[THostConfig], metaclass=abc.ABCMeta):
    """Base class for profiles offering SSH connectivity."""
    @abc.abstractmethod
    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""


class RemoteProfile(SshTargetHostProfile[TRemoteConfig], metaclass=abc.ABCMeta):
    """Base class for remote instance profiles."""
    @property
    def core_ci_state(self) -> t.Optional[dict[str, str]]:
        """The saved Ansible Core CI state."""
        return self.state.get('core_ci')

    @core_ci_state.setter
    def core_ci_state(self, value: dict[str, str]) -> None:
        """The saved Ansible Core CI state."""
        self.state['core_ci'] = value

    def provision(self) -> None:
        """Provision the host before delegation."""
        self.core_ci = self.create_core_ci(load=True)
        self.core_ci.start()

        self.core_ci_state = self.core_ci.save()

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""
        if self.args.remote_terminate == TerminateMode.ALWAYS or (self.args.remote_terminate == TerminateMode.SUCCESS and self.args.success):
            self.delete_instance()

    @property
    def core_ci(self) -> t.Optional[AnsibleCoreCI]:
        """Return the cached AnsibleCoreCI instance, if any, otherwise None."""
        return self.cache.get('core_ci')

    @core_ci.setter
    def core_ci(self, value: AnsibleCoreCI) -> None:
        """Cache the given AnsibleCoreCI instance."""
        self.cache['core_ci'] = value

    def get_instance(self) -> t.Optional[AnsibleCoreCI]:
        """Return the current AnsibleCoreCI instance, loading it if not already loaded."""
        if not self.core_ci and self.core_ci_state:
            self.core_ci = self.create_core_ci(load=False)
            self.core_ci.load(self.core_ci_state)

        return self.core_ci

    def delete_instance(self):
        """Delete the AnsibleCoreCI VM instance."""
        core_ci = self.get_instance()

        if not core_ci:
            return  # instance has not been provisioned

        core_ci.stop()

    def wait_for_instance(self) -> AnsibleCoreCI:
        """Wait for an AnsibleCoreCI VM instance to become ready."""
        core_ci = self.get_instance()
        core_ci.wait()

        return core_ci

    def create_core_ci(self, load: bool) -> AnsibleCoreCI:
        """Create and return an AnsibleCoreCI instance."""
        if not self.config.arch:
            raise InternalError(f'No arch specified for config: {self.config}')

        return AnsibleCoreCI(
            args=self.args,
            resource=VmResource(
                platform=self.config.platform,
                version=self.config.version,
                architecture=self.config.arch,
                provider=self.config.provider,
                tag='controller' if self.controller else 'target',
            ),
            load=load,
        )


class ControllerProfile(SshTargetHostProfile[ControllerConfig], PosixProfile[ControllerConfig]):
    """Host profile for the controller as a target."""
    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        settings = SshConnectionDetail(
            name='localhost',
            host='localhost',
            port=None,
            user='root',
            identity_file=SshKey(self.args).key,
            python_interpreter=self.args.controller_python.path,
        )

        return [SshConnection(self.args, settings)]


class DockerProfile(ControllerHostProfile[DockerConfig], SshTargetHostProfile[DockerConfig]):
    """Host profile for a docker instance."""
    @property
    def container_name(self) -> t.Optional[str]:
        """Return the stored container name, if any, otherwise None."""
        return self.state.get('container_name')

    @container_name.setter
    def container_name(self, value: str) -> None:
        """Store the given container name."""
        self.state['container_name'] = value

    def provision(self) -> None:
        """Provision the host before delegation."""
        container = run_support_container(
            args=self.args,
            context='__test_hosts__',
            image=self.config.image,
            name=f'ansible-test-{"controller" if self.controller else "target"}-{self.args.session_name}',
            ports=[22],
            publish_ports=not self.controller,  # connections to the controller over SSH are not required
            options=self.get_docker_run_options(),
            cleanup=CleanupMode.NO,
        )

        if not container:
            return

        self.container_name = container.name

    def setup(self) -> None:
        """Perform out-of-band setup before delegation."""
        bootstrapper = BootstrapDocker(
            controller=self.controller,
            python_versions=[self.python.version],
            ssh_key=SshKey(self.args),
        )

        setup_sh = bootstrapper.get_script()
        shell = setup_sh.splitlines()[0][2:]

        docker_exec(self.args, self.container_name, [shell], data=setup_sh, capture=False)

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""
        if not self.container_name:
            return  # provision was never called or did not succeed, so there is no container to remove

        if self.args.docker_terminate == TerminateMode.ALWAYS or (self.args.docker_terminate == TerminateMode.SUCCESS and self.args.success):
            docker_rm(self.args, self.container_name)

    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        if not self.controller:
            con = self.get_controller_target_connections()[0]

            for dummy in range(1, 60):
                try:
                    con.run(['id'], capture=True)
                except SubprocessError as ex:
                    if 'Permission denied' in ex.message:
                        raise

                    time.sleep(1)
                else:
                    return

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        containers = get_container_database(self.args)
        access = containers.data[HostType.control]['__test_hosts__'][self.container_name]

        host = access.host_ip
        port = dict(access.port_map())[22]

        settings = SshConnectionDetail(
            name=self.config.name,
            user='root',
            host=host,
            port=port,
            identity_file=SshKey(self.args).key,
            python_interpreter=self.python.path,
        )

        return [SshConnection(self.args, settings)]

    def get_origin_controller_connection(self) -> DockerConnection:
        """Return a connection for accessing the host as a controller from the origin."""
        return DockerConnection(self.args, self.container_name)

    def get_working_directory(self) -> str:
        """Return the working directory for the host."""
        return '/root'

    def get_docker_run_options(self) -> list[str]:
        """Return a list of options needed to run the container."""
        options = [
            '--volume', '/sys/fs/cgroup:/sys/fs/cgroup:ro',
            f'--privileged={str(self.config.privileged).lower()}',
            # These temporary mount points need to be created at run time.
            # Previously they were handled by the VOLUME instruction during container image creation.
            # However, that approach creates anonymous volumes when running the container, which are then left behind after the container is deleted.
            # These options eliminate the need for the VOLUME instruction, and override it if they are present.
            # The mount options used are those typically found on Linux systems.
            # Of special note is the "exec" option for "/tmp", which is required by ansible-test for path injection of executables using temporary directories.
            '--tmpfs', '/tmp:exec',
            '--tmpfs', '/run:exec',
            '--tmpfs', '/run/lock',  # some systemd containers require a separate tmpfs here, such as Ubuntu 20.04 and Ubuntu 22.04
        ]

        if self.config.memory:
            options.extend([
                f'--memory={self.config.memory}',
                f'--memory-swap={self.config.memory}',
            ])

        if self.config.seccomp != 'default':
            options.extend(['--security-opt', f'seccomp={self.config.seccomp}'])

        docker_socket = '/var/run/docker.sock'

        if get_docker_hostname() != 'localhost' or os.path.exists(docker_socket):
            options.extend(['--volume', f'{docker_socket}:{docker_socket}'])

        return options


class NetworkInventoryProfile(HostProfile[NetworkInventoryConfig]):
    """Host profile for a network inventory."""


class NetworkRemoteProfile(RemoteProfile[NetworkRemoteConfig]):
    """Host profile for a network remote instance."""
    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        self.wait_until_ready()

    def get_inventory_variables(self) -> dict[str, t.Optional[t.Union[str, int]]]:
        """Return inventory variables for accessing this host."""
        core_ci = self.wait_for_instance()
        connection = core_ci.connection

        variables: dict[str, t.Optional[t.Union[str, int]]] = dict(
            ansible_connection=self.config.connection,
            ansible_pipelining='yes',
            ansible_host=connection.hostname,
            ansible_port=connection.port,
            ansible_user=connection.username,
            ansible_ssh_private_key_file=core_ci.ssh_key.key,
            ansible_network_os=f'{self.config.collection}.{self.config.platform}' if self.config.collection else self.config.platform,
        )

        return variables

    def wait_until_ready(self) -> None:
        """Wait for the host to respond to an Ansible module request."""
        core_ci = self.wait_for_instance()

        if not isinstance(self.args, IntegrationConfig):
            return  # skip extended checks unless we're running integration tests

        inventory = Inventory.create_single_host(sanitize_host_name(self.config.name), self.get_inventory_variables())
        env = ansible_environment(self.args)
        module_name = f'{self.config.collection + "." if self.config.collection else ""}{self.config.platform}_command'

        with tempfile.NamedTemporaryFile() as inventory_file:
            inventory.write(self.args, inventory_file.name)

            cmd = ['ansible', '-m', module_name, '-a', 'commands=?', '-i', inventory_file.name, 'all']

            for dummy in range(1, 90):
                try:
                    intercept_python(self.args, self.args.controller_python, cmd, env, capture=True)
                except SubprocessError as ex:
                    display.warning(str(ex))
                    time.sleep(10)
                else:
                    return

            raise ApplicationError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        core_ci = self.wait_for_instance()

        settings = SshConnectionDetail(
            name=core_ci.name,
            host=core_ci.connection.hostname,
            port=core_ci.connection.port,
            user=core_ci.connection.username,
            identity_file=core_ci.ssh_key.key,
        )

        return [SshConnection(self.args, settings)]


class OriginProfile(ControllerHostProfile[OriginConfig]):
    """Host profile for origin."""
    def get_origin_controller_connection(self) -> LocalConnection:
        """Return a connection for accessing the host as a controller from the origin."""
        return LocalConnection(self.args)

    def get_working_directory(self) -> str:
        """Return the working directory for the host."""
        return os.getcwd()


class PosixRemoteProfile(ControllerHostProfile[PosixRemoteConfig], RemoteProfile[PosixRemoteConfig]):
    """Host profile for a POSIX remote instance."""
    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        self.wait_until_ready()

    def configure(self) -> None:
        """Perform in-band configuration. Executed before delegation for the controller and after delegation for targets."""
        # a target uses a single python version, but a controller may include additional versions for targets running on the controller
        python_versions = [self.python.version] + [target.python.version for target in self.targets if isinstance(target, ControllerConfig)]
        python_versions = sorted_versions(list(set(python_versions)))

        core_ci = self.wait_for_instance()
        pwd = self.wait_until_ready()

        display.info(f'Remote working directory: {pwd}', verbosity=1)

        bootstrapper = BootstrapRemote(
            controller=self.controller,
            platform=self.config.platform,
            platform_version=self.config.version,
            python_versions=python_versions,
            ssh_key=core_ci.ssh_key,
        )

        setup_sh = bootstrapper.get_script()
        shell = setup_sh.splitlines()[0][2:]

        ssh = self.get_origin_controller_connection()
        ssh.run([shell], data=setup_sh, capture=False)

    def get_ssh_connection(self) -> SshConnection:
        """Return an SSH connection for accessing the host."""
        core_ci = self.wait_for_instance()

        settings = SshConnectionDetail(
            name=core_ci.name,
            user=core_ci.connection.username,
            host=core_ci.connection.hostname,
            port=core_ci.connection.port,
            identity_file=core_ci.ssh_key.key,
            python_interpreter=self.python.path,
        )

        if settings.user == 'root':
            become: t.Optional[Become] = None
        elif self.config.become:
            become = SUPPORTED_BECOME_METHODS[self.config.become]()
        else:
            display.warning(f'Defaulting to "sudo" for platform "{self.config.platform}" become support.', unique=True)
            become = Sudo()

        return SshConnection(self.args, settings, become)

    def wait_until_ready(self) -> str:
        """Wait for instance to respond to SSH, returning the current working directory once connected."""
        core_ci = self.wait_for_instance()

        for dummy in range(1, 90):
            try:
                return self.get_working_directory()
            except SubprocessError as ex:
                if 'Permission denied' in ex.message:
                    raise

                time.sleep(10)

        raise ApplicationError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        return [self.get_ssh_connection()]

    def get_origin_controller_connection(self) -> SshConnection:
        """Return a connection for accessing the host as a controller from the origin."""
        return self.get_ssh_connection()

    def get_working_directory(self) -> str:
        """Return the working directory for the host."""
        if not self.pwd:
            ssh = self.get_origin_controller_connection()
            stdout = ssh.run(['pwd'], capture=True)[0]

            if self.args.explain:
                return '/pwd'

            pwd = stdout.strip().splitlines()[-1]

            if not pwd.startswith('/'):
                raise Exception(f'Unexpected current working directory "{pwd}" from "pwd" command output:\n{stdout.strip()}')

            self.pwd = pwd

        return self.pwd

    @property
    def pwd(self) -> t.Optional[str]:
        """Return the cached pwd, if any, otherwise None."""
        return self.cache.get('pwd')

    @pwd.setter
    def pwd(self, value: str) -> None:
        """Cache the given pwd."""
        self.cache['pwd'] = value


class PosixSshProfile(SshTargetHostProfile[PosixSshConfig], PosixProfile[PosixSshConfig]):
    """Host profile for a POSIX SSH instance."""
    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        settings = SshConnectionDetail(
            name='target',
            user=self.config.user,
            host=self.config.host,
            port=self.config.port,
            identity_file=SshKey(self.args).key,
            python_interpreter=self.python.path,
        )

        return [SshConnection(self.args, settings)]


class WindowsInventoryProfile(SshTargetHostProfile[WindowsInventoryConfig]):
    """Host profile for a Windows inventory."""
    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        inventory = parse_inventory(self.args, self.config.path)
        hosts = get_hosts(inventory, 'windows')
        identity_file = SshKey(self.args).key

        settings = [SshConnectionDetail(
            name=name,
            host=config['ansible_host'],
            port=22,
            user=config['ansible_user'],
            identity_file=identity_file,
            shell_type='powershell',
        ) for name, config in hosts.items()]

        if settings:
            details = '\n'.join(f'{ssh.name} {ssh.user}@{ssh.host}:{ssh.port}' for ssh in settings)
            display.info(f'Generated SSH connection details from inventory:\n{details}', verbosity=1)

        return [SshConnection(self.args, setting) for setting in settings]


class WindowsRemoteProfile(RemoteProfile[WindowsRemoteConfig]):
    """Host profile for a Windows remote instance."""
    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        self.wait_until_ready()

    def get_inventory_variables(self) -> dict[str, t.Optional[t.Union[str, int]]]:
        """Return inventory variables for accessing this host."""
        core_ci = self.wait_for_instance()
        connection = core_ci.connection

        variables: dict[str, t.Optional[t.Union[str, int]]] = dict(
            ansible_connection='winrm',
            ansible_pipelining='yes',
            ansible_winrm_server_cert_validation='ignore',
            ansible_host=connection.hostname,
            ansible_port=connection.port,
            ansible_user=connection.username,
            ansible_password=connection.password,
            ansible_ssh_private_key_file=core_ci.ssh_key.key,
        )

        # HACK: force 2016 to use NTLM + HTTP message encryption
        if self.config.version == '2016':
            variables.update(
                ansible_winrm_transport='ntlm',
                ansible_winrm_scheme='http',
                ansible_port='5985',
            )

        return variables

    def wait_until_ready(self) -> None:
        """Wait for the host to respond to an Ansible module request."""
        core_ci = self.wait_for_instance()

        if not isinstance(self.args, IntegrationConfig):
            return  # skip extended checks unless we're running integration tests

        inventory = Inventory.create_single_host(sanitize_host_name(self.config.name), self.get_inventory_variables())
        env = ansible_environment(self.args)
        module_name = 'ansible.windows.win_ping'

        with tempfile.NamedTemporaryFile() as inventory_file:
            inventory.write(self.args, inventory_file.name)

            cmd = ['ansible', '-m', module_name, '-i', inventory_file.name, 'all']

            for dummy in range(1, 120):
                try:
                    intercept_python(self.args, self.args.controller_python, cmd, env, capture=True)
                except SubprocessError as ex:
                    display.warning(str(ex))
                    time.sleep(10)
                else:
                    return

        raise ApplicationError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        core_ci = self.wait_for_instance()

        settings = SshConnectionDetail(
            name=core_ci.name,
            host=core_ci.connection.hostname,
            port=22,
            user=core_ci.connection.username,
            identity_file=core_ci.ssh_key.key,
            shell_type='powershell',
        )

        return [SshConnection(self.args, settings)]


@cache
def get_config_profile_type_map() -> dict[t.Type[HostConfig], t.Type[HostProfile]]:
    """Create and return a mapping of HostConfig types to HostProfile types."""
    return get_type_map(HostProfile, HostConfig)


def create_host_profile(
        args: EnvironmentConfig,
        config: HostConfig,
        controller: bool,
) -> HostProfile:
    """Create and return a host profile from the given host configuration."""
    profile_type = get_config_profile_type_map()[type(config)]
    profile = profile_type(args=args, config=config, targets=args.targets if controller else None)
    return profile
