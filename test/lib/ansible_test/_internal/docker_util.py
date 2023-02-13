"""Functions for accessing docker via the docker cli."""
from __future__ import annotations

import dataclasses
import enum
import json
import os
import pathlib
import re
import socket
import time
import urllib.parse
import typing as t

from .util import (
    ApplicationError,
    common_environment,
    display,
    find_executable,
    SubprocessError,
    cache,
    OutputStream,
)

from .util_common import (
    run_command,
    raw_command,
)

from .config import (
    CommonConfig,
)

from .thread import (
    mutex,
    named_lock,
)

from .cgroup import (
    CGroupEntry,
    MountEntry,
    MountType,
)

DOCKER_COMMANDS = [
    'docker',
    'podman',
]

UTILITY_IMAGE = 'quay.io/ansible/ansible-test-utility-container:2.0.0'

# Max number of open files in a docker container.
# Passed with --ulimit option to the docker run command.
MAX_NUM_OPEN_FILES = 10240

# The value of /proc/*/loginuid when it is not set.
# It is a reserved UID, which is the maximum 32-bit unsigned integer value.
# See: https://access.redhat.com/solutions/25404
LOGINUID_NOT_SET = 4294967295


class DockerInfo:
    """The results of `docker info` and `docker version` for the container runtime."""

    @classmethod
    def init(cls, args: CommonConfig) -> DockerInfo:
        """Initialize and return a DockerInfo instance."""
        command = require_docker().command

        info_stdout = docker_command(args, ['info', '--format', '{{ json . }}'], capture=True, always=True)[0]
        info = json.loads(info_stdout)

        if server_errors := info.get('ServerErrors'):
            # This can occur when a remote docker instance is in use and the instance is not responding, such as when the system is still starting up.
            # In that case an error such as the following may be returned:
            # error during connect: Get "http://{hostname}:2375/v1.24/info": dial tcp {ip_address}:2375: connect: no route to host
            raise ApplicationError('Unable to get container host information: ' + '\n'.join(server_errors))

        version_stdout = docker_command(args, ['version', '--format', '{{ json . }}'], capture=True, always=True)[0]
        version = json.loads(version_stdout)

        info = DockerInfo(args, command, info, version)

        return info

    def __init__(self, args: CommonConfig, engine: str, info: dict[str, t.Any], version: dict[str, t.Any]) -> None:
        self.args = args
        self.engine = engine
        self.info = info
        self.version = version

    @property
    def client(self) -> dict[str, t.Any]:
        """The client version details."""
        client = self.version.get('Client')

        if not client:
            raise ApplicationError('Unable to get container host client information.')

        return client

    @property
    def server(self) -> dict[str, t.Any]:
        """The server version details."""
        server = self.version.get('Server')

        if not server:
            if self.engine == 'podman':
                # Some Podman versions always report server version info (verified with 1.8.0 and 1.9.3).
                # Others do not unless Podman remote is being used.
                # To provide consistency, use the client version if the server version isn't provided.
                # See: https://github.com/containers/podman/issues/2671#issuecomment-804382934
                return self.client

            raise ApplicationError('Unable to get container host server information.')

        return server

    @property
    def client_version(self) -> str:
        """The client version."""
        return self.client['Version']

    @property
    def server_version(self) -> str:
        """The server version."""
        return self.server['Version']

    @property
    def client_major_minor_version(self) -> tuple[int, int]:
        """The client major and minor version."""
        major, minor = self.client_version.split('.')[:2]
        return int(major), int(minor)

    @property
    def server_major_minor_version(self) -> tuple[int, int]:
        """The server major and minor version."""
        major, minor = self.server_version.split('.')[:2]
        return int(major), int(minor)

    @property
    def cgroupns_option_supported(self) -> bool:
        """Return True if the `--cgroupns` option is supported, otherwise return False."""
        if self.engine == 'docker':
            # Docker added support for the `--cgroupns` option in version 20.10.
            # Both the client and server must support the option to use it.
            # See: https://docs.docker.com/engine/release-notes/#20100
            return self.client_major_minor_version >= (20, 10) and self.server_major_minor_version >= (20, 10)

        raise NotImplementedError(self.engine)

    @property
    def cgroup_version(self) -> int:
        """The cgroup version of the container host."""
        info = self.info
        host = info.get('host')

        # When the container host reports cgroup v1 it is running either cgroup v1 legacy mode or cgroup v2 hybrid mode.
        # When the container host reports cgroup v2 it is running under cgroup v2 unified mode.
        # See: https://github.com/containers/podman/blob/8356621249e36ed62fc7f35f12d17db9027ff076/libpod/info_linux.go#L52-L56
        # See: https://github.com/moby/moby/blob/d082bbcc0557ec667faca81b8b33bec380b75dac/daemon/info_unix.go#L24-L27

        if host:
            return int(host['cgroupVersion'].lstrip('v'))  # podman

        try:
            return int(info['CgroupVersion'])  # docker
        except KeyError:
            pass

        # Docker 20.10 (API version 1.41) added support for cgroup v2.
        # Unfortunately the client or server is too old to report the cgroup version.
        # If the server is old, we can infer the cgroup version.
        # Otherwise, we'll need to fall back to detection.
        # See: https://docs.docker.com/engine/release-notes/#20100
        # See: https://docs.docker.com/engine/api/version-history/#v141-api-changes

        if self.server_major_minor_version < (20, 10):
            return 1  # old docker server with only cgroup v1 support

        # Tell the user what versions they have and recommend they upgrade the client.
        # Downgrading the server should also work, but we won't mention that.
        message = (
            f'The Docker client version is {self.client_version}. '
            f'The Docker server version is {self.server_version}. '
            'Upgrade your Docker client to version 20.10 or later.'
        )

        if detect_host_properties(self.args).cgroup_v2:
            # Unfortunately cgroup v2 was detected on the Docker server.
            # A newer client is needed to support the `--cgroupns` option for use with cgroup v2.
            raise ApplicationError(f'Unsupported Docker client and server combination using cgroup v2. {message}')

        display.warning(f'Detected Docker server cgroup v1 using probing. {message}', unique=True)

        return 1  # docker server is using cgroup v1 (or cgroup v2 hybrid)

    @property
    def docker_desktop_wsl2(self) -> bool:
        """Return True if Docker Desktop integrated with WSL2 is detected, otherwise False."""
        info = self.info

        kernel_version = info.get('KernelVersion')
        operating_system = info.get('OperatingSystem')

        dd_wsl2 = kernel_version and kernel_version.endswith('-WSL2') and operating_system == 'Docker Desktop'

        return dd_wsl2

    @property
    def description(self) -> str:
        """Describe the container runtime."""
        tags = dict(
            client=self.client_version,
            server=self.server_version,
            cgroup=f'v{self.cgroup_version}',
        )

        labels = [self.engine] + [f'{key}={value}' for key, value in tags.items()]

        if self.docker_desktop_wsl2:
            labels.append('DD+WSL2')

        return f'Container runtime: {" ".join(labels)}'


@mutex
def get_docker_info(args: CommonConfig) -> DockerInfo:
    """Return info for the current container runtime. The results are cached."""
    try:
        return get_docker_info.info  # type: ignore[attr-defined]
    except AttributeError:
        pass

    info = DockerInfo.init(args)

    display.info(info.description, verbosity=1)

    get_docker_info.info = info  # type: ignore[attr-defined]

    return info


class SystemdControlGroupV1Status(enum.Enum):
    """The state of the cgroup v1 systemd hierarchy on the container host."""

    SUBSYSTEM_MISSING = 'The systemd cgroup subsystem was not found.'
    FILESYSTEM_NOT_MOUNTED = 'The "/sys/fs/cgroup/systemd" filesystem is not mounted.'
    MOUNT_TYPE_NOT_CORRECT = 'The "/sys/fs/cgroup/systemd" mount type is not correct.'
    VALID = 'The "/sys/fs/cgroup/systemd" mount is valid.'


@dataclasses.dataclass(frozen=True)
class ContainerHostProperties:
    """Container host properties detected at run time."""

    audit_code: str
    max_open_files: int
    loginuid: t.Optional[int]
    cgroup_v1: SystemdControlGroupV1Status
    cgroup_v2: bool


@mutex
def detect_host_properties(args: CommonConfig) -> ContainerHostProperties:
    """
    Detect and return properties of the container host.

    The information collected is:

      - The errno result from attempting to query the container host's audit status.
      - The max number of open files supported by the container host to run containers.
        This value may be capped to the maximum value used by ansible-test.
        If the value is below the desired limit, a warning is displayed.
      - The loginuid used by the container host to run containers, or None if the audit subsystem is unavailable.
      - The cgroup subsystems registered with the Linux kernel.
      - The mounts visible within a container.
      - The status of the systemd cgroup v1 hierarchy.

    This information is collected together to reduce the number of container runs to probe the container host.
    """
    try:
        return detect_host_properties.properties  # type: ignore[attr-defined]
    except AttributeError:
        pass

    single_line_commands = (
        'audit-status',
        'cat /proc/sys/fs/nr_open',
        'ulimit -Hn',
        '(cat /proc/1/loginuid; echo)',
    )

    multi_line_commands = (
        ' && '.join(single_line_commands),
        'cat /proc/1/cgroup',
        'cat /proc/1/mountinfo',
    )

    options = ['--volume', '/sys/fs/cgroup:/probe:ro']
    cmd = ['sh', '-c', ' && echo "-" && '.join(multi_line_commands)]

    stdout = run_utility_container(args, f'ansible-test-probe-{args.session_name}', cmd, options)[0]

    if args.explain:
        return ContainerHostProperties(
            audit_code='???',
            max_open_files=MAX_NUM_OPEN_FILES,
            loginuid=LOGINUID_NOT_SET,
            cgroup_v1=SystemdControlGroupV1Status.VALID,
            cgroup_v2=False,
        )

    blocks = stdout.split('\n-\n')

    values = blocks[0].split('\n')

    audit_parts = values[0].split(' ', 1)
    audit_status = int(audit_parts[0])
    audit_code = audit_parts[1]

    system_limit = int(values[1])
    hard_limit = int(values[2])
    loginuid = int(values[3]) if values[3] else None

    cgroups = CGroupEntry.loads(blocks[1])
    mounts = MountEntry.loads(blocks[2])

    if hard_limit < MAX_NUM_OPEN_FILES and hard_limit < system_limit and require_docker().command == 'docker':
        # Podman will use the highest possible limits, up to its default of 1M.
        # See: https://github.com/containers/podman/blob/009afb50b308548eb129bc68e654db6c6ad82e7a/pkg/specgen/generate/oci.go#L39-L58
        # Docker limits are less predictable. They could be the system limit or the user's soft limit.
        # If Docker is running as root it should be able to use the system limit.
        # When Docker reports a limit below the preferred value and the system limit, attempt to use the preferred value, up to the system limit.
        options = ['--ulimit', f'nofile={min(system_limit, MAX_NUM_OPEN_FILES)}']
        cmd = ['sh', '-c', 'ulimit -Hn']

        try:
            stdout = run_utility_container(args, f'ansible-test-ulimit-{args.session_name}', cmd, options)[0]
        except SubprocessError as ex:
            display.warning(str(ex))
        else:
            hard_limit = int(stdout)

    # Check the audit error code from attempting to query the container host's audit status.
    #
    # The following error codes are known to occur:
    #
    # EPERM - Operation not permitted
    # This occurs when the root user runs a container but lacks the AUDIT_WRITE capability.
    # This will cause patched versions of OpenSSH to disconnect after a login succeeds.
    # See: https://src.fedoraproject.org/rpms/openssh/blob/f36/f/openssh-7.6p1-audit.patch
    #
    # EBADF - Bad file number
    # This occurs when the host doesn't support the audit system (the open_audit call fails).
    # This allows SSH logins to succeed despite the failure.
    # See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/netlink.c#L204-L209
    #
    # ECONNREFUSED - Connection refused
    # This occurs when a non-root user runs a container without the AUDIT_WRITE capability.
    # When sending an audit message, libaudit ignores this error condition.
    # This allows SSH logins to succeed despite the failure.
    # See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/deprecated.c#L48-L52

    subsystems = set(cgroup.subsystem for cgroup in cgroups)
    mount_types = {mount.path: mount.type for mount in mounts}

    if 'systemd' not in subsystems:
        cgroup_v1 = SystemdControlGroupV1Status.SUBSYSTEM_MISSING
    elif not (mount_type := mount_types.get(pathlib.PurePosixPath('/probe/systemd'))):
        cgroup_v1 = SystemdControlGroupV1Status.FILESYSTEM_NOT_MOUNTED
    elif mount_type != MountType.CGROUP_V1:
        cgroup_v1 = SystemdControlGroupV1Status.MOUNT_TYPE_NOT_CORRECT
    else:
        cgroup_v1 = SystemdControlGroupV1Status.VALID

    cgroup_v2 = mount_types.get(pathlib.PurePosixPath('/probe')) == MountType.CGROUP_V2

    display.info(f'Container host audit status: {audit_code} ({audit_status})', verbosity=1)
    display.info(f'Container host max open files: {hard_limit}', verbosity=1)
    display.info(f'Container loginuid: {loginuid if loginuid is not None else "unavailable"}'
                 f'{" (not set)" if loginuid == LOGINUID_NOT_SET else ""}', verbosity=1)

    if hard_limit < MAX_NUM_OPEN_FILES:
        display.warning(f'Unable to set container max open files to {MAX_NUM_OPEN_FILES}. Using container host limit of {hard_limit} instead.')
    else:
        hard_limit = MAX_NUM_OPEN_FILES

    properties = ContainerHostProperties(
        # The errno (audit_status) is intentionally not exposed here, as it can vary across systems and architectures.
        # Instead, the symbolic name (audit_code) is used, which is resolved inside the container which generated the error.
        # See: https://man7.org/linux/man-pages/man3/errno.3.html
        audit_code=audit_code,
        max_open_files=hard_limit,
        loginuid=loginuid,
        cgroup_v1=cgroup_v1,
        cgroup_v2=cgroup_v2,
    )

    detect_host_properties.properties = properties  # type: ignore[attr-defined]

    return properties


def run_utility_container(
    args: CommonConfig,
    name: str,
    cmd: list[str],
    options: list[str],
    data: t.Optional[str] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Run the specified command using the ansible-test utility container, returning stdout and stderr."""
    options = options + [
        '--name', name,
        '--rm',
    ]  # fmt: skip

    if data:
        options.append('-i')

    docker_pull(args, UTILITY_IMAGE)

    return docker_run(args, UTILITY_IMAGE, options, cmd, data)


class DockerCommand:
    """Details about the available docker command."""

    def __init__(self, command: str, executable: str, version: str) -> None:
        self.command = command
        self.executable = executable
        self.version = version

    @staticmethod
    def detect() -> t.Optional[DockerCommand]:
        """Detect and return the available docker command, or None."""
        if os.environ.get('ANSIBLE_TEST_PREFER_PODMAN'):
            commands = list(reversed(DOCKER_COMMANDS))
        else:
            commands = DOCKER_COMMANDS

        for command in commands:
            executable = find_executable(command, required=False)

            if executable:
                version = raw_command([command, '-v'], env=docker_environment(), capture=True)[0].strip()

                if command == 'docker' and 'podman' in version:
                    continue  # avoid detecting podman as docker

                display.info('Detected "%s" container runtime version: %s' % (command, version), verbosity=1)

                return DockerCommand(command, executable, version)

        return None


def require_docker() -> DockerCommand:
    """Return the docker command to invoke. Raises an exception if docker is not available."""
    if command := get_docker_command():
        return command

    raise ApplicationError(f'No container runtime detected. Supported commands: {", ".join(DOCKER_COMMANDS)}')


@cache
def get_docker_command() -> t.Optional[DockerCommand]:
    """Return the docker command to invoke, or None if docker is not available."""
    return DockerCommand.detect()


def docker_available() -> bool:
    """Return True if docker is available, otherwise return False."""
    return bool(get_docker_command())


@cache
def get_docker_host_ip() -> str:
    """Return the IP of the Docker host."""
    docker_host_ip = socket.gethostbyname(get_docker_hostname())

    display.info('Detected docker host IP: %s' % docker_host_ip, verbosity=1)

    return docker_host_ip


@cache
def get_docker_hostname() -> str:
    """Return the hostname of the Docker service."""
    docker_host = os.environ.get('DOCKER_HOST')

    if docker_host and docker_host.startswith('tcp://'):
        try:
            hostname = urllib.parse.urlparse(docker_host)[1].split(':')[0]
            display.info('Detected Docker host: %s' % hostname, verbosity=1)
        except ValueError:
            hostname = 'localhost'
            display.warning('Could not parse DOCKER_HOST environment variable "%s", falling back to localhost.' % docker_host)
    else:
        hostname = 'localhost'
        display.info('Assuming Docker is available on localhost.', verbosity=1)

    return hostname


@cache
def get_podman_host_ip() -> str:
    """Return the IP of the Podman host."""
    podman_host_ip = socket.gethostbyname(get_podman_hostname())

    display.info('Detected Podman host IP: %s' % podman_host_ip, verbosity=1)

    return podman_host_ip


@cache
def get_podman_default_hostname() -> t.Optional[str]:
    """
    Return the default hostname of the Podman service.

    --format was added in podman 3.3.0, this functionality depends on its availability
    """
    hostname: t.Optional[str] = None
    try:
        stdout = raw_command(['podman', 'system', 'connection', 'list', '--format=json'], env=docker_environment(), capture=True)[0]
    except SubprocessError:
        stdout = '[]'

    try:
        connections = json.loads(stdout)
    except json.decoder.JSONDecodeError:
        return hostname

    for connection in connections:
        # A trailing indicates the default
        if connection['Name'][-1] == '*':
            hostname = connection['URI']
            break

    return hostname


@cache
def get_podman_remote() -> t.Optional[str]:
    """Return the remote podman hostname, if any, otherwise return None."""
    # URL value resolution precedence:
    # - command line value
    # - environment variable CONTAINER_HOST
    # - containers.conf
    # - unix://run/podman/podman.sock
    hostname = None

    podman_host = os.environ.get('CONTAINER_HOST')
    if not podman_host:
        podman_host = get_podman_default_hostname()

    if podman_host and podman_host.startswith('ssh://'):
        try:
            hostname = urllib.parse.urlparse(podman_host).hostname
        except ValueError:
            display.warning('Could not parse podman URI "%s"' % podman_host)
        else:
            display.info('Detected Podman remote: %s' % hostname, verbosity=1)
    return hostname


@cache
def get_podman_hostname() -> str:
    """Return the hostname of the Podman service."""
    hostname = get_podman_remote()

    if not hostname:
        hostname = 'localhost'
        display.info('Assuming Podman is available on localhost.', verbosity=1)

    return hostname


@cache
def get_docker_container_id() -> t.Optional[str]:
    """Return the current container ID if running in a container, otherwise return None."""
    mountinfo_path = pathlib.Path('/proc/self/mountinfo')
    container_id = None
    engine = None

    if mountinfo_path.is_file():
        # NOTE: This method of detecting the container engine and container ID relies on implementation details of each container engine.
        #       Although the implementation details have remained unchanged for some time, there is no guarantee they will continue to work.
        #       There have been proposals to create a standard mechanism for this, but none is currently available.
        #       See: https://github.com/opencontainers/runtime-spec/issues/1105

        mounts = MountEntry.loads(mountinfo_path.read_text())

        for mount in mounts:
            if str(mount.path) == '/etc/hostname':
                # Podman generates /etc/hostname in the makePlatformBindMounts function.
                # That function ends up using ContainerRunDirectory to generate a path like: {prefix}/{container_id}/userdata/hostname
                # NOTE: The {prefix} portion of the path can vary, so should not be relied upon.
                # See: https://github.com/containers/podman/blob/480c7fbf5361f3bd8c1ed81fe4b9910c5c73b186/libpod/container_internal_linux.go#L660-L664
                # See: https://github.com/containers/podman/blob/480c7fbf5361f3bd8c1ed81fe4b9910c5c73b186/vendor/github.com/containers/storage/store.go#L3133
                # This behavior has existed for ~5 years and was present in Podman version 0.2.
                # See: https://github.com/containers/podman/pull/248
                if match := re.search('/(?P<id>[0-9a-f]{64})/userdata/hostname$', str(mount.root)):
                    container_id = match.group('id')
                    engine = 'Podman'
                    break

                # Docker generates /etc/hostname in the BuildHostnameFile function.
                # That function ends up using the containerRoot function to generate a path like: {prefix}/{container_id}/hostname
                # NOTE: The {prefix} portion of the path can vary, so should not be relied upon.
                # See: https://github.com/moby/moby/blob/cd8a090e6755bee0bdd54ac8a894b15881787097/container/container_unix.go#L58
                # See: https://github.com/moby/moby/blob/92e954a2f05998dc05773b6c64bbe23b188cb3a0/daemon/container.go#L86
                # This behavior has existed for at least ~7 years and was present in Docker version 1.0.1.
                # See: https://github.com/moby/moby/blob/v1.0.1/daemon/container.go#L351
                # See: https://github.com/moby/moby/blob/v1.0.1/daemon/daemon.go#L133
                if match := re.search('/(?P<id>[0-9a-f]{64})/hostname$', str(mount.root)):
                    container_id = match.group('id')
                    engine = 'Docker'
                    break

    if container_id:
        display.info(f'Detected execution in {engine} container ID: {container_id}', verbosity=1)

    return container_id


def docker_pull(args: CommonConfig, image: str) -> None:
    """
    Pull the specified image if it is not available.
    Images without a tag or digest will not be pulled.
    Retries up to 10 times if the pull fails.
    A warning will be shown for any image with volumes defined.
    Images will be pulled only once.
    Concurrent pulls for the same image will block until the first completes.
    """
    with named_lock(f'docker_pull:{image}') as first:
        if first:
            __docker_pull(args, image)


def __docker_pull(args: CommonConfig, image: str) -> None:
    """Internal implementation for docker_pull. Do not call directly."""
    if '@' not in image and ':' not in image:
        display.info('Skipping pull of image without tag or digest: %s' % image, verbosity=2)
        inspect = docker_image_inspect(args, image)
    elif inspect := docker_image_inspect(args, image, always=True):
        display.info('Skipping pull of existing image: %s' % image, verbosity=2)
    else:
        for _iteration in range(1, 10):
            try:
                docker_command(args, ['pull', image], capture=False)

                if (inspect := docker_image_inspect(args, image)) or args.explain:
                    break

                display.warning(f'Image "{image}" not found after pull completed. Waiting a few seconds before trying again.')
            except SubprocessError:
                display.warning(f'Failed to pull container image "{image}". Waiting a few seconds before trying again.')
                time.sleep(3)
        else:
            raise ApplicationError(f'Failed to pull container image "{image}".')

    if inspect and inspect.volumes:
        display.warning(f'Image "{image}" contains {len(inspect.volumes)} volume(s): {", ".join(sorted(inspect.volumes))}\n'
                        'This may result in leaking anonymous volumes. It may also prevent the image from working on some hosts or container engines.\n'
                        'The image should be rebuilt without the use of the VOLUME instruction.',
                        unique=True)


def docker_cp_to(args: CommonConfig, container_id: str, src: str, dst: str) -> None:
    """Copy a file to the specified container."""
    docker_command(args, ['cp', src, '%s:%s' % (container_id, dst)], capture=True)


def docker_create(
    args: CommonConfig,
    image: str,
    options: list[str],
    cmd: list[str] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Create a container using the given docker image."""
    return docker_command(args, ['create'] + options + [image] + cmd, capture=True)


def docker_run(
    args: CommonConfig,
    image: str,
    options: list[str],
    cmd: list[str] = None,
    data: t.Optional[str] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Run a container using the given docker image."""
    return docker_command(args, ['run'] + options + [image] + cmd, data=data, capture=True)


def docker_start(
    args: CommonConfig,
    container_id: str,
    options: list[str],
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Start a container by name or ID."""
    return docker_command(args, ['start'] + options + [container_id], capture=True)


def docker_rm(args: CommonConfig, container_id: str) -> None:
    """Remove the specified container."""
    try:
        # Stop the container with SIGKILL immediately, then remove the container.
        # Podman supports the `--time` option on `rm`, but only since version 4.0.0.
        # Docker does not support the `--time` option on `rm`.
        docker_command(args, ['stop', '--time', '0', container_id], capture=True)
        docker_command(args, ['rm', container_id], capture=True)
    except SubprocessError as ex:
        # Both Podman and Docker report an error if the container does not exist.
        # The error messages contain the same "no such container" string, differing only in capitalization.
        if 'no such container' not in ex.stderr.lower():
            raise ex


class DockerError(Exception):
    """General Docker error."""


class ContainerNotFoundError(DockerError):
    """The container identified by `identifier` was not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__('The container "%s" was not found.' % identifier)

        self.identifier = identifier


class DockerInspect:
    """The results of `docker inspect` for a single container."""

    def __init__(self, args: CommonConfig, inspection: dict[str, t.Any]) -> None:
        self.args = args
        self.inspection = inspection

    # primary properties

    @property
    def id(self) -> str:
        """Return the ID of the container."""
        return self.inspection['Id']

    @property
    def network_settings(self) -> dict[str, t.Any]:
        """Return a dictionary of the container network settings."""
        return self.inspection['NetworkSettings']

    @property
    def state(self) -> dict[str, t.Any]:
        """Return a dictionary of the container state."""
        return self.inspection['State']

    @property
    def config(self) -> dict[str, t.Any]:
        """Return a dictionary of the container configuration."""
        return self.inspection['Config']

    # nested properties

    @property
    def ports(self) -> dict[str, list[dict[str, str]]]:
        """Return a dictionary of ports the container has published."""
        return self.network_settings['Ports']

    @property
    def networks(self) -> t.Optional[dict[str, dict[str, t.Any]]]:
        """Return a dictionary of the networks the container is attached to, or None if running under podman, which does not support networks."""
        return self.network_settings.get('Networks')

    @property
    def running(self) -> bool:
        """Return True if the container is running, otherwise False."""
        return self.state['Running']

    @property
    def pid(self) -> int:
        """Return the PID of the init process."""
        if self.args.explain:
            return 0

        return self.state['Pid']

    @property
    def env(self) -> list[str]:
        """Return a list of the environment variables used to create the container."""
        return self.config['Env']

    @property
    def image(self) -> str:
        """Return the image used to create the container."""
        return self.config['Image']

    # functions

    def env_dict(self) -> dict[str, str]:
        """Return a dictionary of the environment variables used to create the container."""
        return dict((item[0], item[1]) for item in [e.split('=', 1) for e in self.env])

    def get_tcp_port(self, port: int) -> t.Optional[list[dict[str, str]]]:
        """Return a list of the endpoints published by the container for the specified TCP port, or None if it is not published."""
        return self.ports.get('%d/tcp' % port)

    def get_network_names(self) -> t.Optional[list[str]]:
        """Return a list of the network names the container is attached to."""
        if self.networks is None:
            return None

        return sorted(self.networks)

    def get_network_name(self) -> str:
        """Return the network name the container is attached to. Raises an exception if no network, or more than one, is attached."""
        networks = self.get_network_names()

        if not networks:
            raise ApplicationError('No network found for Docker container: %s.' % self.id)

        if len(networks) > 1:
            raise ApplicationError('Found multiple networks for Docker container %s instead of only one: %s' % (self.id, ', '.join(networks)))

        return networks[0]


def docker_inspect(args: CommonConfig, identifier: str, always: bool = False) -> DockerInspect:
    """
    Return the results of `docker container inspect` for the specified container.
    Raises a ContainerNotFoundError if the container was not found.
    """
    try:
        stdout = docker_command(args, ['container', 'inspect', identifier], capture=True, always=always)[0]
    except SubprocessError as ex:
        stdout = ex.stdout

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) == 1:
        return DockerInspect(args, items[0])

    raise ContainerNotFoundError(identifier)


def docker_network_disconnect(args: CommonConfig, container_id: str, network: str) -> None:
    """Disconnect the specified docker container from the given network."""
    docker_command(args, ['network', 'disconnect', network, container_id], capture=True)


class DockerImageInspect:
    """The results of `docker image inspect` for a single image."""

    def __init__(self, args: CommonConfig, inspection: dict[str, t.Any]) -> None:
        self.args = args
        self.inspection = inspection

    # primary properties

    @property
    def config(self) -> dict[str, t.Any]:
        """Return a dictionary of the image config."""
        return self.inspection['Config']

    # nested properties

    @property
    def volumes(self) -> dict[str, t.Any]:
        """Return a dictionary of the image volumes."""
        return self.config.get('Volumes') or {}

    @property
    def cmd(self) -> list[str]:
        """The command to run when the container starts."""
        return self.config['Cmd']


@mutex
def docker_image_inspect(args: CommonConfig, image: str, always: bool = False) -> t.Optional[DockerImageInspect]:
    """
    Return the results of `docker image inspect` for the specified image or None if the image does not exist.
    """
    inspect_cache: dict[str, DockerImageInspect]

    try:
        inspect_cache = docker_image_inspect.cache  # type: ignore[attr-defined]
    except AttributeError:
        inspect_cache = docker_image_inspect.cache = {}  # type: ignore[attr-defined]

    if inspect_result := inspect_cache.get(image):
        return inspect_result

    try:
        stdout = docker_command(args, ['image', 'inspect', image], capture=True, always=always)[0]
    except SubprocessError:
        stdout = '[]'

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) > 1:
        raise ApplicationError(f'Inspection of image "{image}" resulted in {len(items)} items:\n{json.dumps(items, indent=4)}')

    if len(items) == 1:
        inspect_result = DockerImageInspect(args, items[0])
        inspect_cache[image] = inspect_result
        return inspect_result

    return None


class DockerNetworkInspect:
    """The results of `docker network inspect` for a single network."""

    def __init__(self, args: CommonConfig, inspection: dict[str, t.Any]) -> None:
        self.args = args
        self.inspection = inspection


def docker_network_inspect(args: CommonConfig, network: str, always: bool = False) -> t.Optional[DockerNetworkInspect]:
    """
    Return the results of `docker network inspect` for the specified network or None if the network does not exist.
    """
    try:
        stdout = docker_command(args, ['network', 'inspect', network], capture=True, always=always)[0]
    except SubprocessError:
        stdout = '[]'

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) == 1:
        return DockerNetworkInspect(args, items[0])

    return None


def docker_logs(args: CommonConfig, container_id: str) -> None:
    """Display logs for the specified container. If an error occurs, it is displayed rather than raising an exception."""
    try:
        docker_command(args, ['logs', container_id], capture=False)
    except SubprocessError as ex:
        display.error(str(ex))


def docker_exec(
    args: CommonConfig,
    container_id: str,
    cmd: list[str],
    capture: bool,
    options: t.Optional[list[str]] = None,
    stdin: t.Optional[t.IO[bytes]] = None,
    stdout: t.Optional[t.IO[bytes]] = None,
    interactive: bool = False,
    output_stream: t.Optional[OutputStream] = None,
    data: t.Optional[str] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Execute the given command in the specified container."""
    if not options:
        options = []

    if data or stdin or stdout:
        options.append('-i')

    return docker_command(
        args,
        ['exec'] + options + [container_id] + cmd,
        capture=capture,
        stdin=stdin,
        stdout=stdout,
        interactive=interactive,
        output_stream=output_stream,
        data=data,
    )


def docker_command(
    args: CommonConfig,
    cmd: list[str],
    capture: bool,
    stdin: t.Optional[t.IO[bytes]] = None,
    stdout: t.Optional[t.IO[bytes]] = None,
    interactive: bool = False,
    output_stream: t.Optional[OutputStream] = None,
    always: bool = False,
    data: t.Optional[str] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Run the specified docker command."""
    env = docker_environment()
    command = [require_docker().command]

    if command[0] == 'podman' and get_podman_remote():
        command.append('--remote')

    return run_command(
        args,
        command + cmd,
        env=env,
        capture=capture,
        stdin=stdin,
        stdout=stdout,
        interactive=interactive,
        always=always,
        output_stream=output_stream,
        data=data,
    )


def docker_environment() -> dict[str, str]:
    """Return a dictionary of docker related environment variables found in the current environment."""
    env = common_environment()

    var_names = {
        'XDG_RUNTIME_DIR',  # podman
    }

    var_prefixes = {
        'CONTAINER_',  # podman remote
        'DOCKER_',  # docker
    }

    env.update({name: value for name, value in os.environ.items() if name in var_names or any(name.startswith(prefix) for prefix in var_prefixes)})

    return env
