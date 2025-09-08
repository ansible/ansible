"""Profiles to represent individual test hosts or a user-provided inventory file."""

from __future__ import annotations

import abc
import dataclasses
import json
import os
import pathlib
import shlex
import tempfile
import time
import typing as t

from .io import (
    read_text_file,
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
    HostConnectionError,
    ANSIBLE_TEST_TARGET_ROOT,
    WINDOWS_CONNECTION_VARIABLES,
    ANSIBLE_SOURCE_ROOT,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
)

from .util_common import (
    get_docs_url,
    intercept_python,
)

from .docker_util import (
    docker_exec,
    docker_image_inspect,
    docker_logs,
    docker_pull,
    docker_rm,
    get_docker_hostname,
    require_docker,
    get_docker_info,
    detect_host_properties,
    run_utility_container,
    SystemdControlGroupV1Status,
    LOGINUID_NOT_SET,
    UTILITY_IMAGE,
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
    create_ssh_port_forwards,
    SshProcess,
)

from .ansible_util import (
    ansible_environment,
    get_hosts,
    parse_inventory,
)

from .containers import (
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

from .completion import (
    AuditMode,
    CGroupVersion,
)

from .dev.container_probe import (
    CGroupMount,
    CGroupPath,
    CGroupState,
    MountType,
    check_container_cgroup_status,
)

from .debugging import (
    DebuggerProfile,
    DebuggerSettings,
)


class ControlGroupError(ApplicationError):
    """Raised when the container host does not have the necessary cgroup support to run a container."""

    def __init__(self, args: CommonConfig, reason: str) -> None:
        engine = require_docker().command
        dd_wsl2 = get_docker_info(args).docker_desktop_wsl2

        message = f'''
{reason}

Run the following commands as root on the container host to resolve this issue:

  mkdir /sys/fs/cgroup/systemd
  mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr
  chown -R {{user}}:{{group}} /sys/fs/cgroup/systemd  # only when rootless

NOTE: These changes must be applied each time the container host is rebooted.
'''.strip()

        podman_message = '''
      If rootless Podman is already running [1], you may need to stop it before
      containers are able to use the new mount point.

[1] Check for 'podman' and 'catatonit' processes.
'''

        dd_wsl_message = f'''
      When using Docker Desktop with WSL2, additional configuration [1] is required.

[1] {get_docs_url("https://docs.ansible.com/ansible-core/devel/dev_guide/testing_running_locally.html#docker-desktop-with-wsl2")}
'''

        if engine == 'podman':
            message += podman_message
        elif dd_wsl2:
            message += dd_wsl_message

        message = message.strip()

        super().__init__(message)


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
                kvp = ' '.join(f"{key}={value!r}" for key, value in variables.items())
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


class HostProfile[THostConfig: HostConfig](metaclass=abc.ABCMeta):
    """Base class for host profiles."""

    def __init__(
        self,
        *,
        args: EnvironmentConfig,
        config: THostConfig,
        controller: ControllerHostProfile,
    ) -> None:
        self.args = args
        self.config = config
        self.controller = not controller  # this profile is a controller whenever the `controller` arg was not provided
        self.targets = args.targets if self.controller else []  # only keep targets if this profile is a controller
        self.controller_profile = controller if isinstance(self, ControllerProfile) else None

        self.state: dict[str, t.Any] = {}
        """State that must be persisted across delegation."""
        self.cache: dict[str, t.Any] = {}
        """Cache that must not be persisted across delegation."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The name of the host profile."""

    def pre_provision(self) -> None:
        """Pre-provision the host profile."""

    def provision(self) -> None:
        """Provision the host before delegation."""

    def setup(self) -> None:
        """Perform out-of-band setup before delegation."""

    def on_target_failure(self) -> None:
        """Executed during failure handling if this profile is a target."""

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

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.name}'


class DebuggableProfile[THostConfig: HostConfig](HostProfile[THostConfig], DebuggerProfile, metaclass=abc.ABCMeta):
    """Base class for profiles remote debugging."""

    __DEBUGGING_PORT_KEY = 'debugging_port'
    __DEBUGGING_FORWARDER_KEY = 'debugging_forwarder'

    @property
    def debugger(self) -> DebuggerSettings | None:
        """The debugger settings for this host if present and enabled, otherwise None."""
        return self.args.metadata.debugger_settings

    @property
    def debugging_enabled(self) -> bool:
        """Returns `True` if debugging is enabled for this profile, otherwise `False`."""
        if self.controller:
            return self.args.metadata.debugger_flags.enable

        return self.args.metadata.debugger_flags.ansiballz

    @property
    def debugger_host(self) -> str:
        """The debugger host to use."""
        return 'localhost'

    @property
    def debugger_port(self) -> int:
        """The debugger port to use."""
        return self.state.get(self.__DEBUGGING_PORT_KEY) or self.origin_debugger_port

    @property
    def debugging_forwarder(self) -> SshProcess | None:
        """The SSH forwarding process, if enabled."""
        return self.cache.get(self.__DEBUGGING_FORWARDER_KEY)

    @debugging_forwarder.setter
    def debugging_forwarder(self, value: SshProcess) -> None:
        """The SSH forwarding process, if enabled."""
        self.cache[self.__DEBUGGING_FORWARDER_KEY] = value

    @property
    def origin_debugger_port(self) -> int:
        """The debugger port on the origin."""
        return self.debugger.port

    def enable_debugger_forwarding(self, ssh: SshConnectionDetail) -> None:
        """Enable debugger port forwarding from the origin."""
        if not self.debugging_enabled:
            return

        endpoint = ('localhost', self.origin_debugger_port)
        forwards = [endpoint]

        self.debugging_forwarder = create_ssh_port_forwards(self.args, ssh, forwards)

        port_forwards = self.debugging_forwarder.collect_port_forwards()

        self.state[self.__DEBUGGING_PORT_KEY] = port = port_forwards[endpoint]

        display.info(f'Remote debugging of {self.name!r} is available on port {port}.', verbosity=1)

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""
        super().deprovision()

        if not self.debugging_forwarder:
            return  # forwarding not in use

        self.debugging_forwarder.terminate()

        display.info(f'Waiting for the {self.name!r} remote debugging SSH port forwarding process to terminate.', verbosity=1)

        self.debugging_forwarder.wait()

    def get_source_mapping(self) -> dict[str, str]:
        """Get the source mapping from the given metadata."""
        from . import data_context

        if collection := data_context().content.collection:
            source_mapping = {
                f"{self.args.metadata.ansible_test_root}/": f'{ANSIBLE_TEST_ROOT}/',
                f"{self.args.metadata.ansible_lib_root}/": f'{ANSIBLE_LIB_ROOT}/',
                f'{self.args.metadata.collection_root}/ansible_collections/': f'{collection.root}/ansible_collections/',
            }
        else:
            ansible_source_root = pathlib.Path(self.args.metadata.ansible_lib_root).parent.parent

            source_mapping = {
                f"{ansible_source_root}/": f'{ANSIBLE_SOURCE_ROOT}/',
            }

        source_mapping = {key: value for key, value in source_mapping.items() if key != value}

        return source_mapping

    def activate_debugger(self) -> None:
        """Activate the debugger after delegation."""
        if not self.args.metadata.loaded or not self.args.metadata.debugger_flags.self:
            return

        display.info('Activating remote debugging of ansible-test.', verbosity=1)

        os.environ.update(self.debugger.get_environment_variables(self))

        self.debugger.activate_debugger(self)

        pass  # pylint: disable=unnecessary-pass  # when suspend is True, execution pauses here -- it's also a convenient place to put a breakpoint

    def get_ansiballz_inventory_variables(self) -> dict[str, t.Any]:
        """
        Return inventory variables for remote debugging of AnsiballZ modules.
        When delegating, this function must be called after delegation.
        """
        if not self.args.metadata.debugger_flags.ansiballz:
            return {}

        debug_type = self.debugger.get_debug_type()

        return {
            f"_ansible_ansiballz_{debug_type}_config": json.dumps(self.get_ansiballz_debugger_config()),
        }

    def get_ansiballz_environment_variables(self) -> dict[str, t.Any]:
        """
        Return environment variables for remote debugging of AnsiballZ modules.
        When delegating, this function must be called after delegation.
        """
        if not self.args.metadata.debugger_flags.ansiballz:
            return {}

        debug_type = self.debugger.get_debug_type().upper()

        return {
            f"_ANSIBLE_ANSIBALLZ_{debug_type}_CONFIG": json.dumps(self.get_ansiballz_debugger_config()),
        }

    def get_ansiballz_debugger_config(self) -> dict[str, t.Any]:
        """
        Return config for remote debugging of AnsiballZ modules.
        When delegating, this function must be called after delegation.
        """
        debugger_config = self.debugger.get_ansiballz_config(self)

        display.info(f'>>> Debugger Config ({self.name} AnsiballZ)\n{json.dumps(debugger_config, indent=4)}', verbosity=3)

        return debugger_config

    def get_ansible_cli_environment_variables(self) -> dict[str, t.Any]:
        """
        Return environment variables for remote debugging of the Ansible CLI.
        When delegating, this function must be called after delegation.
        """
        if not self.args.metadata.debugger_flags.cli:
            return {}

        debugger_config = dict(
            args=self.debugger.get_cli_arguments(self),
            env=self.debugger.get_environment_variables(self),
        )

        display.info(f'>>> Debugger Config ({self.name} Ansible CLI)\n{json.dumps(debugger_config, indent=4)}', verbosity=3)

        return dict(
            ANSIBLE_TEST_DEBUGGER_CONFIG=json.dumps(debugger_config),
        )


class PosixProfile[TPosixConfig: PosixConfig](HostProfile[TPosixConfig], metaclass=abc.ABCMeta):
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


class ControllerHostProfile[T: ControllerHostConfig](PosixProfile[T], DebuggableProfile[T], metaclass=abc.ABCMeta):
    """Base class for profiles usable as a controller."""

    @abc.abstractmethod
    def get_origin_controller_connection(self) -> Connection:
        """Return a connection for accessing the host as a controller from the origin."""

    @abc.abstractmethod
    def get_working_directory(self) -> str:
        """Return the working directory for the host."""


class SshTargetHostProfile[THostConfig: HostConfig](HostProfile[THostConfig], metaclass=abc.ABCMeta):
    """Base class for profiles offering SSH connectivity."""

    @abc.abstractmethod
    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""


class RemoteProfile[TRemoteConfig: RemoteConfig](SshTargetHostProfile[TRemoteConfig], metaclass=abc.ABCMeta):
    """Base class for remote instance profiles."""

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.config.name

    @property
    def core_ci_state(self) -> t.Optional[dict[str, str]]:
        """The saved Ansible Core CI state."""
        return self.state.get('core_ci')

    @core_ci_state.setter
    def core_ci_state(self, value: dict[str, str]) -> None:
        """The saved Ansible Core CI state."""
        self.state['core_ci'] = value

    def pre_provision(self) -> None:
        """Pre-provision the host before delegation."""
        self.core_ci = self.create_core_ci(load=True)
        self.core_ci.start()

        self.core_ci_state = self.core_ci.save()

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""
        super().deprovision()

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

    def delete_instance(self) -> None:
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


class ControllerProfile(SshTargetHostProfile[ControllerConfig], PosixProfile[ControllerConfig], DebuggableProfile[ControllerConfig]):
    """Host profile for the controller as a target."""

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.controller_profile.name

    @property
    def debugger_port(self) -> int:
        """The pydevd port to use."""
        return self.controller_profile.debugger_port

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


class DockerProfile(ControllerHostProfile[DockerConfig], SshTargetHostProfile[DockerConfig], DebuggableProfile[DockerConfig]):
    """Host profile for a docker instance."""

    MARKER = 'ansible-test-marker'

    @dataclasses.dataclass(frozen=True)
    class InitConfig:
        """Configuration details required to run the container init."""

        options: list[str]
        command: str
        command_privileged: bool
        expected_mounts: tuple[CGroupMount, ...]

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.config.name

    @property
    def container_name(self) -> t.Optional[str]:
        """Return the stored container name, if any, otherwise None."""
        return self.state.get('container_name')

    @container_name.setter
    def container_name(self, value: str) -> None:
        """Store the given container name."""
        self.state['container_name'] = value

    @property
    def cgroup_path(self) -> t.Optional[str]:
        """Return the path to the cgroup v1 systemd hierarchy, if any, otherwise None."""
        return self.state.get('cgroup_path')

    @cgroup_path.setter
    def cgroup_path(self, value: str) -> None:
        """Store the path to the cgroup v1 systemd hierarchy."""
        self.state['cgroup_path'] = value

    @property
    def label(self) -> str:
        """Label to apply to resources related to this profile."""
        return f'{"controller" if self.controller else "target"}'

    def provision(self) -> None:
        """Provision the host before delegation."""
        init_probe = self.args.dev_probe_cgroups is not None
        init_config = self.get_init_config()

        container = run_support_container(
            args=self.args,
            context='__test_hosts__',
            image=self.config.image,
            name=f'ansible-test-{self.label}',
            ports=[22],
            publish_ports=self.debugging_enabled or not self.controller,  # SSH to the controller is not required unless remote debugging is enabled
            options=init_config.options,
            cleanup=False,
            cmd=self.build_init_command(init_config, init_probe),
        )

        if not container:
            if self.args.prime_containers:
                if init_config.command_privileged or init_probe:
                    docker_pull(self.args, UTILITY_IMAGE)

            return

        self.container_name = container.name

        try:
            options = ['--pid', 'host', '--privileged']

            if init_config.command and init_config.command_privileged:
                init_command = init_config.command

                if not init_probe:
                    init_command += f' && {shlex.join(self.wake_command)}'

                cmd = ['nsenter', '-t', str(container.details.container.pid), '-m', '-p', 'sh', '-c', init_command]
                run_utility_container(self.args, f'ansible-test-init-{self.label}', cmd, options)

            if init_probe:
                check_container_cgroup_status(self.args, self.config, self.container_name, init_config.expected_mounts)

                cmd = ['nsenter', '-t', str(container.details.container.pid), '-m', '-p'] + self.wake_command
                run_utility_container(self.args, f'ansible-test-wake-{self.label}', cmd, options)
        except SubprocessError:
            display.info(f'Checking container "{self.container_name}" logs...')
            docker_logs(self.args, self.container_name)

            raise

    def get_init_config(self) -> InitConfig:
        """Return init config for running under the current container engine."""
        self.check_cgroup_requirements()

        engine = require_docker().command
        init_config = getattr(self, f'get_{engine}_init_config')()

        return init_config

    def get_podman_init_config(self) -> InitConfig:
        """Return init config for running under Podman."""
        options = self.get_common_run_options()
        command: t.Optional[str] = None
        command_privileged = False
        expected_mounts: tuple[CGroupMount, ...]

        cgroup_version = get_docker_info(self.args).cgroup_version

        # Podman 4.4.0 updated containers/common to 0.51.0, which removed the SYS_CHROOT capability from the default list.
        # This capability is needed by services such as sshd, so is unconditionally added here.
        # See: https://github.com/containers/podman/releases/tag/v4.4.0
        # See: https://github.com/containers/common/releases/tag/v0.51.0
        # See: https://github.com/containers/common/pull/1240
        options.extend(('--cap-add', 'SYS_CHROOT'))

        # Without AUDIT_WRITE the following errors may appear in the system logs of a container after attempting to log in using SSH:
        #
        #   fatal: linux_audit_write_entry failed: Operation not permitted
        #
        # This occurs when running containers as root when the container host provides audit support, but the user lacks the AUDIT_WRITE capability.
        # The AUDIT_WRITE capability is provided by docker by default, but not podman.
        # See: https://github.com/moby/moby/pull/7179
        #
        # OpenSSH Portable requires AUDIT_WRITE when logging in with a TTY if the Linux audit feature was compiled in.
        # Containers with the feature enabled will require the AUDIT_WRITE capability when EPERM is returned while accessing the audit system.
        # See: https://github.com/openssh/openssh-portable/blob/2dc328023f60212cd29504fc05d849133ae47355/audit-linux.c#L90
        # See: https://github.com/openssh/openssh-portable/blob/715c892f0a5295b391ae92c26ef4d6a86ea96e8e/loginrec.c#L476-L478
        #
        # Some containers will be running a patched version of OpenSSH which blocks logins when EPERM is received while using the audit system.
        # These containers will require the AUDIT_WRITE capability when EPERM is returned while accessing the audit system.
        # See: https://src.fedoraproject.org/rpms/openssh/blob/f36/f/openssh-7.6p1-audit.patch
        #
        # Since only some containers carry the patch or enable the Linux audit feature in OpenSSH, this capability is enabled on a per-container basis.
        # No warning is provided when adding this capability, since there's not really anything the user can do about it.
        if self.config.audit == AuditMode.REQUIRED and detect_host_properties(self.args).audit_code == 'EPERM':
            options.extend(('--cap-add', 'AUDIT_WRITE'))

        # Without AUDIT_CONTROL the following errors may appear in the system logs of a container after attempting to log in using SSH:
        #
        #   pam_loginuid(sshd:session): Error writing /proc/self/loginuid: Operation not permitted
        #   pam_loginuid(sshd:session): set_loginuid failed
        #
        # Containers configured to use the pam_loginuid module will encounter this error. If the module is required, logins will fail.
        # Since most containers will have this configuration, the code to handle this issue is applied to all containers.
        #
        # This occurs when the loginuid is set on the container host and doesn't match the user on the container host which is running the container.
        # Container hosts which do not use systemd are likely to leave the loginuid unset and thus be unaffected.
        # The most common source of a mismatch is the use of sudo to run ansible-test, which changes the uid but cannot change the loginuid.
        # This condition typically occurs only under podman, since the loginuid is inherited from the current user.
        # See: https://github.com/containers/podman/issues/13012#issuecomment-1034049725
        #
        # This condition is detected by querying the loginuid of a container running on the container host.
        # When it occurs, a warning is displayed and the AUDIT_CONTROL capability is added to containers to work around the issue.
        # The warning serves as notice to the user that their usage of ansible-test is responsible for the additional capability requirement.
        if (loginuid := detect_host_properties(self.args).loginuid) not in (0, LOGINUID_NOT_SET, None):
            display.warning(f'Running containers with capability AUDIT_CONTROL since the container loginuid ({loginuid}) is incorrect. '
                            'This is most likely due to use of sudo to run ansible-test when loginuid is already set.', unique=True)

            options.extend(('--cap-add', 'AUDIT_CONTROL'))

        if self.config.cgroup == CGroupVersion.NONE:
            # Containers which do not require cgroup do not use systemd.

            options.extend((
                # Disabling systemd support in Podman will allow these containers to work on hosts without systemd.
                # Without this, running a container on a host without systemd results in errors such as (from crun):
                #   Error: crun: error stat'ing file `/sys/fs/cgroup/systemd`: No such file or directory:
                # A similar error occurs when using runc:
                #   OCI runtime attempted to invoke a command that was not found
                '--systemd', 'false',
                # A private cgroup namespace limits what is visible in /proc/*/cgroup.
                '--cgroupns', 'private',
                # Mounting a tmpfs overrides the cgroup mount(s) that would otherwise be provided by Podman.
                # This helps provide a consistent container environment across various container host configurations.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V1_ONLY) and cgroup_version == 1:
            # Podman hosts providing cgroup v1 will automatically bind mount the systemd hierarchy read-write in the container.
            # They will also create a dedicated cgroup v1 systemd hierarchy for the container.
            # On hosts with systemd this path is: /sys/fs/cgroup/systemd/libpod_parent/libpod-{container_id}/
            # On hosts without systemd this path is: /sys/fs/cgroup/systemd/{container_id}/

            options.extend((
                # Force Podman to enable systemd support since a command may be used later (to support pre-init diagnostics).
                '--systemd', 'always',
                # The host namespace must be used to permit the container to access the cgroup v1 systemd hierarchy created by Podman.
                '--cgroupns', 'host',
                # Mask the host cgroup tmpfs mount to avoid exposing the host cgroup v1 hierarchies (or cgroup v2 hybrid) to the container.
                # Podman will provide a cgroup v1 systemd hierarchy on top of this.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            self.check_systemd_cgroup_v1(options)  # podman

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                # The mount point can be writable or not.
                # The reason for the variation is not known.
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=None, state=CGroupState.HOST),
                # The filesystem type can be tmpfs or devtmpfs.
                # The reason for the variation is not known.
                CGroupMount(path=CGroupPath.SYSTEMD_RELEASE_AGENT, type=None, writable=False, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V2_ONLY) and cgroup_version == 2:
            # Podman hosts providing cgroup v2 will give each container a read-write cgroup mount.

            options.extend((
                # Force Podman to enable systemd support since a command may be used later (to support pre-init diagnostics).
                '--systemd', 'always',
                # A private cgroup namespace is used to avoid exposing the host cgroup to the container.
                '--cgroupns', 'private',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
            )
        elif self.config.cgroup == CGroupVersion.V1_ONLY and cgroup_version == 2:
            # Containers which require cgroup v1 need explicit volume mounts on container hosts not providing that version.
            # We must put the container PID 1 into the cgroup v1 systemd hierarchy we create.
            cgroup_path = self.create_systemd_cgroup_v1()  # podman
            command = f'echo 1 > {cgroup_path}/cgroup.procs'

            options.extend((
                # Force Podman to enable systemd support since a command is being provided.
                '--systemd', 'always',
                # A private cgroup namespace is required. Using the host cgroup namespace results in errors such as the following (from crun):
                #   Error: OCI runtime error: mount `/sys/fs/cgroup` to '/sys/fs/cgroup': Invalid argument
                # A similar error occurs when using runc:
                #   Error: OCI runtime error: runc create failed: unable to start container process: error during container init:
                #   error mounting "/sys/fs/cgroup" to rootfs at "/sys/fs/cgroup": mount /sys/fs/cgroup:/sys/fs/cgroup (via /proc/self/fd/7), flags: 0x1000:
                #   invalid argument
                '--cgroupns', 'private',
                # Unlike Docker, Podman ignores a /sys/fs/cgroup tmpfs mount, instead exposing a cgroup v2 mount.
                # The exposed volume will be read-write, but the container will have its own private namespace.
                # Provide a read-only cgroup v1 systemd hierarchy under which the dedicated ansible-test cgroup will be mounted read-write.
                # Without this systemd will fail while attempting to mount the cgroup v1 systemd hierarchy.
                # Podman doesn't support using a tmpfs for this. Attempting to do so results in an error (from crun):
                #   Error: OCI runtime error: read: Invalid argument
                # A similar error occurs when using runc:
                #   Error: OCI runtime error: runc create failed: unable to start container process: error during container init:
                #   error mounting "tmpfs" to rootfs at "/sys/fs/cgroup/systemd": tmpcopyup: failed to copy /sys/fs/cgroup/systemd to /proc/self/fd/7
                #   (/tmp/runctop3876247619/runctmpdir1460907418): read /proc/self/fd/7/cgroup.kill: invalid argument
                '--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:ro',
                # Provide the container access to the cgroup v1 systemd hierarchy created by ansible-test.
                '--volume', f'{cgroup_path}:{cgroup_path}:rw',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=False, state=CGroupState.SHADOWED),
                CGroupMount(path=cgroup_path, type=MountType.CGROUP_V1, writable=True, state=CGroupState.HOST),
            )
        else:
            raise InternalError(f'Unhandled cgroup configuration: {self.config.cgroup} on cgroup v{cgroup_version}.')

        return self.InitConfig(
            options=options,
            command=command,
            command_privileged=command_privileged,
            expected_mounts=expected_mounts,
        )

    def get_docker_init_config(self) -> InitConfig:
        """Return init config for running under Docker."""
        options = self.get_common_run_options()
        command: t.Optional[str] = None
        command_privileged = False
        expected_mounts: tuple[CGroupMount, ...]

        cgroup_version = get_docker_info(self.args).cgroup_version

        if self.config.cgroup == CGroupVersion.NONE:
            # Containers which do not require cgroup do not use systemd.

            if get_docker_info(self.args).cgroupns_option_supported:
                # Use the `--cgroupns` option if it is supported.
                # Older servers which do not support the option use the host group namespace.
                # Older clients which do not support the option cause newer servers to use the host cgroup namespace (cgroup v1 only).
                # See: https://github.com/moby/moby/blob/master/api/server/router/container/container_routes.go#L512-L517
                # If the host cgroup namespace is used, cgroup information will be visible, but the cgroup mounts will be unavailable due to the tmpfs below.
                options.extend((
                    # A private cgroup namespace limits what is visible in /proc/*/cgroup.
                    '--cgroupns', 'private',
                ))

            options.extend((
                # Mounting a tmpfs overrides the cgroup mount(s) that would otherwise be provided by Docker.
                # This helps provide a consistent container environment across various container host configurations.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V1_ONLY) and cgroup_version == 1:
            # Docker hosts providing cgroup v1 will automatically bind mount the systemd hierarchy read-only in the container.
            # They will also create a dedicated cgroup v1 systemd hierarchy for the container.
            # The cgroup v1 system hierarchy path is: /sys/fs/cgroup/systemd/{container_id}/

            if get_docker_info(self.args).cgroupns_option_supported:
                # Use the `--cgroupns` option if it is supported.
                # Older servers which do not support the option use the host group namespace.
                # Older clients which do not support the option cause newer servers to use the host cgroup namespace (cgroup v1 only).
                # See: https://github.com/moby/moby/blob/master/api/server/router/container/container_routes.go#L512-L517
                options.extend((
                    # The host cgroup namespace must be used.
                    # Otherwise, /proc/1/cgroup will report "/" for the cgroup path, which is incorrect.
                    # See: https://github.com/systemd/systemd/issues/19245#issuecomment-815954506
                    # It is set here to avoid relying on the current Docker configuration.
                    '--cgroupns', 'host',
                ))

            options.extend((
                # Mask the host cgroup tmpfs mount to avoid exposing the host cgroup v1 hierarchies (or cgroup v2 hybrid) to the container.
                '--tmpfs', '/sys/fs/cgroup',
                # A cgroup v1 systemd hierarchy needs to be mounted read-write over the read-only one provided by Docker.
                # Alternatives were tested, but were unusable due to various issues:
                #  - Attempting to remount the existing mount point read-write will result in a "mount point is busy" error.
                #  - Adding the entire "/sys/fs/cgroup" mount will expose hierarchies other than systemd.
                #    If the host is a cgroup v2 hybrid host it would also expose the /sys/fs/cgroup/unified/ hierarchy read-write.
                #    On older systems, such as an Ubuntu 18.04 host, a dedicated v2 cgroup would not be used, exposing the host cgroups to the container.
                '--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:rw',
            ))

            self.check_systemd_cgroup_v1(options)  # docker

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=True, state=CGroupState.HOST),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V2_ONLY) and cgroup_version == 2:
            # Docker hosts providing cgroup v2 will give each container a read-only cgroup mount.
            # It must be remounted read-write before systemd starts.
            # This must be done in a privileged container, otherwise a "permission denied" error can occur.
            command = 'mount -o remount,rw /sys/fs/cgroup/'
            command_privileged = True

            options.extend((
                # A private cgroup namespace is used to avoid exposing the host cgroup to the container.
                # This matches the behavior in Podman 1.7.0 and later, which select cgroupns 'host' mode for cgroup v1 and 'private' mode for cgroup v2.
                # See: https://github.com/containers/podman/pull/4374
                # See: https://github.com/containers/podman/blob/main/RELEASE_NOTES.md#170
                '--cgroupns', 'private',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
            )
        elif self.config.cgroup == CGroupVersion.V1_ONLY and cgroup_version == 2:
            # Containers which require cgroup v1 need explicit volume mounts on container hosts not providing that version.
            # We must put the container PID 1 into the cgroup v1 systemd hierarchy we create.
            cgroup_path = self.create_systemd_cgroup_v1()  # docker
            command = f'echo 1 > {cgroup_path}/cgroup.procs'

            options.extend((
                # A private cgroup namespace is used since no access to the host cgroup namespace is required.
                # This matches the configuration used for running cgroup v1 containers under Podman.
                '--cgroupns', 'private',
                # Provide a read-write tmpfs filesystem to support additional cgroup mount points.
                # Without this Docker will provide a read-only cgroup2 mount instead.
                '--tmpfs', '/sys/fs/cgroup',
                # Provide a read-write tmpfs filesystem to simulate a systemd cgroup v1 hierarchy.
                # Without this systemd will fail while attempting to mount the cgroup v1 systemd hierarchy.
                '--tmpfs', '/sys/fs/cgroup/systemd',
                # Provide the container access to the cgroup v1 systemd hierarchy created by ansible-test.
                '--volume', f'{cgroup_path}:{cgroup_path}:rw',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=cgroup_path, type=MountType.CGROUP_V1, writable=True, state=CGroupState.HOST),
            )
        else:
            raise InternalError(f'Unhandled cgroup configuration: {self.config.cgroup} on cgroup v{cgroup_version}.')

        return self.InitConfig(
            options=options,
            command=command,
            command_privileged=command_privileged,
            expected_mounts=expected_mounts,
        )

    def build_init_command(self, init_config: InitConfig, sleep: bool) -> t.Optional[list[str]]:
        """
        Build and return the command to start in the container.
        Returns None if the default command for the container should be used.

        The sleep duration below was selected to:

          - Allow enough time to perform necessary operations in the container before waking it.
          - Make the delay obvious if the wake command doesn't run or succeed.
          - Avoid hanging indefinitely or for an unreasonably long time.

        NOTE: The container must have a POSIX-compliant default shell "sh" with a non-builtin "sleep" command.
              The "sleep" command is invoked through "env" to avoid using a shell builtin "sleep" (if present).
        """
        command = ''

        if init_config.command and not init_config.command_privileged:
            command += f'{init_config.command} && '

        if sleep or init_config.command_privileged:
            command += 'env sleep 60 ; '

        if not command:
            return None

        docker_pull(self.args, self.config.image)
        inspect = docker_image_inspect(self.args, self.config.image)

        command += f'exec {shlex.join(inspect.cmd)}'

        return ['sh', '-c', command]

    @property
    def wake_command(self) -> list[str]:
        """
        The command used to wake the container from sleep.
        This will be run inside our utility container, so the command used does not need to be present in the container being woken up.
        """
        return ['pkill', 'sleep']

    def check_systemd_cgroup_v1(self, options: list[str]) -> None:
        """Check the cgroup v1 systemd hierarchy to verify it is writeable for our container."""
        probe_script = (read_text_file(os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'check_systemd_cgroup_v1.sh'))
                        .replace('@MARKER@', self.MARKER)
                        .replace('@LABEL@', f'{self.label}-{self.args.session_name}'))

        cmd = ['sh']

        try:
            run_utility_container(self.args, f'ansible-test-cgroup-check-{self.label}', cmd, options, data=probe_script)
        except SubprocessError as ex:
            if error := self.extract_error(ex.stderr):
                raise ControlGroupError(self.args, 'Unable to create a v1 cgroup within the systemd hierarchy.\n'
                                                   f'Reason: {error}') from ex  # cgroup probe failed

            raise

    def create_systemd_cgroup_v1(self) -> str:
        """Create a unique ansible-test cgroup in the v1 systemd hierarchy and return its path."""
        self.cgroup_path = f'/sys/fs/cgroup/systemd/ansible-test-{self.label}-{self.args.session_name}'

        # Privileged mode is required to create the cgroup directories on some hosts, such as Fedora 36 and RHEL 9.0.
        # The mkdir command will fail with "Permission denied" otherwise.
        options = ['--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:rw', '--privileged']
        cmd = ['sh', '-c', f'>&2 echo {shlex.quote(self.MARKER)} && mkdir {shlex.quote(self.cgroup_path)}']

        try:
            run_utility_container(self.args, f'ansible-test-cgroup-create-{self.label}', cmd, options)
        except SubprocessError as ex:
            if error := self.extract_error(ex.stderr):
                raise ControlGroupError(self.args, f'Unable to create a v1 cgroup within the systemd hierarchy.\n'
                                                   f'Reason: {error}') from ex  # cgroup create permission denied

            raise

        return self.cgroup_path

    @property
    def delete_systemd_cgroup_v1_command(self) -> list[str]:
        """The command used to remove the previously created ansible-test cgroup in the v1 systemd hierarchy."""
        return ['find', self.cgroup_path, '-type', 'd', '-delete']

    def delete_systemd_cgroup_v1(self) -> None:
        """Delete a previously created ansible-test cgroup in the v1 systemd hierarchy."""
        # Privileged mode is required to remove the cgroup directories on some hosts, such as Fedora 36 and RHEL 9.0.
        # The BusyBox find utility will report "Permission denied" otherwise, although it still exits with a status code of 0.
        options = ['--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:rw', '--privileged']
        cmd = ['sh', '-c', f'>&2 echo {shlex.quote(self.MARKER)} && {shlex.join(self.delete_systemd_cgroup_v1_command)}']

        try:
            run_utility_container(self.args, f'ansible-test-cgroup-delete-{self.label}', cmd, options)
        except SubprocessError as ex:
            if error := self.extract_error(ex.stderr):
                if error.endswith(': No such file or directory'):
                    return

            display.error(str(ex))

    def extract_error(self, value: str) -> t.Optional[str]:
        """
        Extract the ansible-test portion of the error message from the given value and return it.
        Returns None if no ansible-test marker was found.
        """
        lines = value.strip().splitlines()

        try:
            idx = lines.index(self.MARKER)
        except ValueError:
            return None

        lines = lines[idx + 1:]
        message = '\n'.join(lines)

        return message

    def check_cgroup_requirements(self) -> None:
        """Check cgroup requirements for the container."""
        cgroup_version = get_docker_info(self.args).cgroup_version

        if cgroup_version not in (1, 2):
            raise ApplicationError(f'The container host provides cgroup v{cgroup_version}, but only version v1 and v2 are supported.')

        # Stop early for containers which require cgroup v2 when the container host does not provide it.
        # None of the containers included with ansible-test currently use this configuration.
        # Support for v2-only was added in preparation for the eventual removal of cgroup v1 support from systemd after EOY 2023.
        # See: https://github.com/systemd/systemd/pull/24086
        if self.config.cgroup == CGroupVersion.V2_ONLY and cgroup_version != 2:
            raise ApplicationError(f'Container {self.config.name} requires cgroup v2 but the container host provides cgroup v{cgroup_version}.')

        # Containers which use old versions of systemd (earlier than version 226) require cgroup v1 support.
        # If the host is a cgroup v2 (unified) host, changes must be made to how the container is run.
        #
        # See: https://github.com/systemd/systemd/blob/main/NEWS
        #      Under the "CHANGES WITH 226" section:
        #      > systemd now optionally supports the new Linux kernel "unified" control group hierarchy.
        #
        # NOTE: The container host must have the cgroup v1 mount already present.
        #       If the container is run rootless, the user it runs under must have permissions to the mount.
        #
        # The following commands can be used to make the mount available:
        #
        #   mkdir /sys/fs/cgroup/systemd
        #   mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr
        #   chown -R {user}:{group} /sys/fs/cgroup/systemd  # only when rootless
        #
        # See: https://github.com/containers/crun/blob/main/crun.1.md#runocisystemdforce_cgroup_v1path
        if self.config.cgroup == CGroupVersion.V1_ONLY or (self.config.cgroup != CGroupVersion.NONE and get_docker_info(self.args).cgroup_version == 1):
            if (cgroup_v1 := detect_host_properties(self.args).cgroup_v1) != SystemdControlGroupV1Status.VALID:
                if self.config.cgroup == CGroupVersion.V1_ONLY:
                    if get_docker_info(self.args).cgroup_version == 2:
                        reason = f'Container {self.config.name} requires cgroup v1, but the container host only provides cgroup v2.'
                    else:
                        reason = f'Container {self.config.name} requires cgroup v1, but the container host does not appear to be running systemd.'
                else:
                    reason = 'The container host provides cgroup v1, but does not appear to be running systemd.'

                reason += f'\n{cgroup_v1.value}'

                raise ControlGroupError(self.args, reason)  # cgroup probe reported invalid state

    def setup(self) -> None:
        """Perform out-of-band setup before delegation."""
        bootstrapper = BootstrapDocker(
            controller=self.controller,
            python_interpreters={self.python.version: self.python.path},
            ssh_key=SshKey(self.args),
        )

        setup_sh = bootstrapper.get_script()
        shell = setup_sh.splitlines()[0][2:]

        try:
            docker_exec(self.args, self.container_name, [shell], data=setup_sh, capture=False)
        except SubprocessError:
            display.info(f'Checking container "{self.container_name}" logs...')
            docker_logs(self.args, self.container_name)
            raise

        if self.debugging_enabled:
            self.enable_debugger_forwarding(self.get_ssh_connection_detail(HostType.origin))

    def deprovision(self) -> None:
        """Deprovision the host after delegation has completed."""
        super().deprovision()

        container_exists = False

        if self.container_name:
            if self.args.docker_terminate == TerminateMode.ALWAYS or (self.args.docker_terminate == TerminateMode.SUCCESS and self.args.success):
                docker_rm(self.args, self.container_name)
            else:
                container_exists = True

        if self.cgroup_path:
            if container_exists:
                display.notice(f'Remember to run `{require_docker().command} rm -f {self.container_name}` when finished testing. '
                               f'Then run `{shlex.join(self.delete_systemd_cgroup_v1_command)}` on the container host.')
            else:
                self.delete_systemd_cgroup_v1()
        elif container_exists:
            display.notice(f'Remember to run `{require_docker().command} rm -f {self.container_name}` when finished testing.')

    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        if not self.controller:
            con = self.get_controller_target_connections()[0]
            last_error = ''

            for dummy in range(1, 10):
                try:
                    con.run(['id'], capture=True)
                except SubprocessError as ex:
                    if 'Permission denied' in ex.message:
                        raise

                    last_error = str(ex)
                    time.sleep(1)
                else:
                    return

            display.info('Checking SSH debug output...')
            display.info(last_error)

            if not self.args.delegate and not self.args.host_path:

                def callback() -> None:
                    """Callback to run during error display."""
                    self.on_target_failure()  # when the controller is not delegated, report failures immediately

            else:
                callback = None

            raise HostConnectionError(f'Timeout waiting for {self.config.name} container {self.container_name}.', callback)

    def get_ssh_connection_detail(self, host_type: str) -> SshConnectionDetail:
        """Return SSH connection detail for the specified host type."""
        containers = get_container_database(self.args)
        access = containers.data[host_type]['__test_hosts__'][self.container_name]

        host = access.host_ip
        port = dict(access.port_map())[22]

        settings = SshConnectionDetail(
            name=self.config.name,
            user='root',
            host=host,
            port=port,
            identity_file=SshKey(self.args).key,
            python_interpreter=self.python.path,
            # CentOS 6 uses OpenSSH 5.3, making it incompatible with the default configuration of OpenSSH 8.8 and later clients.
            # Since only CentOS 6 is affected, and it is only supported by ansible-core 2.12, support for RSA SHA-1 is simply hard-coded here.
            # A substring is used to allow custom containers to work, not just the one provided with ansible-test.
            enable_rsa_sha1='centos6' in self.config.image,
        )

        return settings

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        return [SshConnection(self.args, self.get_ssh_connection_detail(HostType.control))]

    def get_origin_controller_connection(self) -> DockerConnection:
        """Return a connection for accessing the host as a controller from the origin."""
        return DockerConnection(self.args, self.container_name)

    def get_working_directory(self) -> str:
        """Return the working directory for the host."""
        return '/root'

    def on_target_failure(self) -> None:
        """Executed during failure handling if this profile is a target."""
        display.info(f'Checking container "{self.container_name}" logs...')

        try:
            docker_logs(self.args, self.container_name)
        except SubprocessError as ex:
            display.error(str(ex))

        if self.config.cgroup != CGroupVersion.NONE:
            # Containers with cgroup support are assumed to be running systemd.
            display.info(f'Checking container "{self.container_name}" systemd logs...')

            try:
                docker_exec(self.args, self.container_name, ['journalctl'], capture=False)
            except SubprocessError as ex:
                display.error(str(ex))

        display.error(f'Connection to container "{self.container_name}" failed. See logs and original error above.')

    def get_common_run_options(self) -> list[str]:
        """Return a list of options needed to run the container."""
        options = [
            # These temporary mount points need to be created at run time when using Docker.
            # They are automatically provided by Podman, but will be overridden by VOLUME instructions for the container, if they exist.
            # If supporting containers with VOLUME instructions is not desired, these options could be limited to use with Docker.
            # See: https://github.com/containers/podman/pull/1318
            # Previously they were handled by the VOLUME instruction during container image creation.
            # However, that approach creates anonymous volumes when running the container, which are then left behind after the container is deleted.
            # These options eliminate the need for the VOLUME instruction, and override it if they are present.
            # The mount options used are those typically found on Linux systems.
            # Of special note is the "exec" option for "/tmp", which is required by ansible-test for path injection of executables using temporary directories.
            '--tmpfs', '/tmp:exec',
            '--tmpfs', '/run:exec',
            '--tmpfs', '/run/lock',  # some systemd containers require a separate tmpfs here, such as Ubuntu 20.04 and Ubuntu 22.04
        ]

        if self.config.privileged:
            options.append('--privileged')

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

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.config.path


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
            # VyOS 1.1.8 uses OpenSSH 5.5, making it incompatible with RSA SHA-256/512 used by Paramiko 2.9 and later.
            # IOS CSR 1000V uses an ancient SSH server, making it incompatible with RSA SHA-256/512 used by Paramiko 2.9 and later.
            # That means all network platforms currently offered by ansible-core-ci require support for RSA SHA-1, so it is simply hard-coded here.
            # NOTE: This option only exists in ansible-core 2.14 and later. For older ansible-core versions, use of Paramiko 2.8.x or earlier is required.
            #       See: https://github.com/ansible/ansible/pull/78789
            #       See: https://github.com/ansible/ansible/pull/78842
            ansible_paramiko_use_rsa_sha2_algorithms='no',
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

            raise HostConnectionError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing the host as a target from the controller."""
        core_ci = self.wait_for_instance()

        settings = SshConnectionDetail(
            name=core_ci.name,
            host=core_ci.connection.hostname,
            port=core_ci.connection.port,
            user=core_ci.connection.username,
            identity_file=core_ci.ssh_key.key,
            # VyOS 1.1.8 uses OpenSSH 5.5, making it incompatible with the default configuration of OpenSSH 8.8 and later clients.
            # IOS CSR 1000V uses an ancient SSH server, making it incompatible with the default configuration of OpenSSH 8.8 and later clients.
            # That means all network platforms currently offered by ansible-core-ci require support for RSA SHA-1, so it is simply hard-coded here.
            enable_rsa_sha1=True,
        )

        return [SshConnection(self.args, settings)]


class OriginProfile(ControllerHostProfile[OriginConfig]):
    """Host profile for origin."""

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return 'origin'

    def get_origin_controller_connection(self) -> LocalConnection:
        """Return a connection for accessing the host as a controller from the origin."""
        return LocalConnection(self.args)

    def get_working_directory(self) -> str:
        """Return the working directory for the host."""
        return os.getcwd()


class PosixRemoteProfile(ControllerHostProfile[PosixRemoteConfig], RemoteProfile[PosixRemoteConfig], DebuggableProfile[PosixRemoteConfig]):
    """Host profile for a POSIX remote instance."""

    def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        self.wait_until_ready()

    def setup(self) -> None:
        """Perform out-of-band setup before delegation."""
        if self.debugging_enabled:
            self.enable_debugger_forwarding(self.get_origin_controller_connection().settings)

    def configure(self) -> None:
        """Perform in-band configuration. Executed before delegation for the controller and after delegation for targets."""
        # a target uses a single python version, but a controller may include additional versions for targets running on the controller
        python_interpreters = {self.python.version: self.python.path}
        python_interpreters.update({target.python.version: target.python.path for target in self.targets if isinstance(target, ControllerConfig)})
        python_interpreters = {version: python_interpreters[version] for version in sorted_versions(list(python_interpreters.keys()))}

        core_ci = self.wait_for_instance()
        pwd = self.wait_until_ready()

        display.info(f'Remote working directory: {pwd}', verbosity=1)

        bootstrapper = BootstrapRemote(
            controller=self.controller,
            platform=self.config.platform,
            platform_version=self.config.version,
            python_interpreters=python_interpreters,
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
                # No "Permission denied" check is performed here.
                # Unlike containers, with remote instances, user configuration isn't guaranteed to have been completed before SSH connections are attempted.
                display.warning(str(ex))
                time.sleep(10)

        raise HostConnectionError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

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

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.config.host

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

    @property
    def name(self) -> str:
        """The name of the host profile."""
        return self.config.path

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
            ansible_host=connection.hostname,
            # ansible_port is intentionally not set using connection.port -- connection-specific variables can set this instead
            ansible_user=connection.username,
            ansible_ssh_private_key_file=core_ci.ssh_key.key,  # required for scenarios which change the connection plugin to SSH
            ansible_test_connection_password=connection.password,  # required for scenarios which change the connection plugin to require a password
        )

        variables.update(ansible_connection=self.config.connection.split('+')[0])
        variables.update(WINDOWS_CONNECTION_VARIABLES[self.config.connection])

        if variables.pop('use_password'):
            variables.update(ansible_password=connection.password)

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

        raise HostConnectionError(f'Timeout waiting for {self.config.name} instance {core_ci.instance_id}.')

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
    controller: ControllerHostProfile | None,
) -> HostProfile:
    """Create and return a host profile from the given host configuration."""
    profile_type = get_config_profile_type_map()[type(config)]
    profile = profile_type(args=args, config=config, controller=controller)
    return profile
