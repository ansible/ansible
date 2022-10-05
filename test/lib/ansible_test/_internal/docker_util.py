"""Functions for accessing docker via the docker cli."""
from __future__ import annotations

import enum
import errno
import json
import os
import random
import socket
import time
import urllib.parse
import typing as t

from .io import (
    read_text_file,
)

from .util import (
    ApplicationError,
    common_environment,
    display,
    find_executable,
    SubprocessError,
    cache,
    mutex,
    OutputStream,
)

from .util_common import (
    run_command,
    raw_command,
)

from .config import (
    CommonConfig,
    EnvironmentConfig,
)

from .thread import (
    named_lock,
)

DOCKER_COMMANDS = [
    'docker',
    'podman',
]

UTILITY_IMAGE = 'quay.io/ansible/ansible-test-utility-container:1.0.0'

# Max number of open files in a docker container.
# Passed with --ulimit option to the docker run command.
MAX_NUM_OPEN_FILES = 10240


class DockerInfo:
    """The results of `docker info` for the container runtime."""
    def __init__(self, data: dict[str, t.Any]) -> None:
        self.data = data

    @property
    def cgroup_version(self) -> int:
        """The cgroup version of the container host."""
        data = self.data
        host = data.get('host')

        if host:
            version = int(host['cgroupVersion'].lstrip('v'))  # podman
        else:
            version = int(data['CgroupVersion'])  # docker

        return version

    @property
    def cgroup_driver(self) -> str:
        """The cgroup driver of the container host."""
        data = self.data
        host = data.get('host')

        if host:
            driver = host['cgroupManager']  # podman
        else:
            driver = data['CgroupDriver']  # docker

        return driver

    @property
    def default_runtime(self) -> str:
        """The default runtime of the container host."""
        data = self.data
        host = data.get('host')

        if host:
            runtime = host['ociRuntime']['name']  # podman
        else:
            runtime = data['DefaultRuntime']  # docker

        return runtime


@mutex
def get_docker_info(args: CommonConfig) -> DockerInfo:
    """Return info for the current container runtime. The results are cached."""
    try:
        return get_docker_info.info  # type: ignore[attr-defined]
    except AttributeError:
        info = get_docker_info.info = DockerInfo(docker_info(args))  # type: ignore[attr-defined]

    return info


class SystemdControlGroupV1Status(enum.Enum):
    """The state of the cgroup v1 systemd hierarchy on the container host."""
    DIRECTORY_NOT_FOUND = 'The "/sys/fs/cgroup/systemd" directory was not found.'
    FILESYSTEM_NOT_MOUNTED = 'The "/sys/fs/cgroup/systemd" filesystem is not mounted.'
    MOUNT_TYPE_NOT_CORRECT = 'The "/sys/fs/cgroup/systemd" mount type is not correct.'
    OWNERSHIP_NOT_CORRECT = 'The "/sys/fs/cgroup/systemd" mount ownership is not correct.'
    VALID = 'The "/sys/fs/cgroup/systemd" mount is valid.'


@mutex
def detect_host_systemd_cgroup_v1(args: EnvironmentConfig) -> SystemdControlGroupV1Status:
    """Detect the state of the cgroup v1 systemd hierarchy on the container host."""
    try:
        return detect_host_systemd_cgroup_v1.cgroup_v1  # type: ignore[attr-defined]
    except AttributeError:
        pass

    cgroup_host_path = '/sys/fs/cgroup'
    cgroup_container_path = '/probe'

    systemd_cgroup_v1_dir = 'systemd'
    systemd_cgroup_v1_type = 'cgroup'
    systemd_cgroup_v1_path = f'{cgroup_container_path}/{systemd_cgroup_v1_dir}'

    options = ['--volume', f'{cgroup_host_path}:{cgroup_container_path}:ro']

    # pipeline the commands to speed up execution
    cmd = ['sh', '-c', f'cat /proc/self/mounts && echo "-" && ls -ln {cgroup_container_path}']
    stdout = run_utility_container(args, f'ansible-test-cgroup-{args.session_name}', options=options, cmd=cmd).strip()
    display.info(stdout, verbosity=4)

    lines = stdout.splitlines()
    split_index = lines.index('-')
    mount_lines = lines[:split_index]
    directory_lines = lines[split_index + 2:]  # skip separator and first line of 'ls' output

    mounts = {item[1]: item for item in [line.split() for line in mount_lines]} if not args.explain else {}
    mount = mounts.get(systemd_cgroup_v1_path)
    display.info(f'Container host systemd cgroup mount: {mount}', verbosity=3)

    directories = {item[8]: item for item in [line.split() for line in directory_lines]} if not args.explain else {}
    directory = directories.get(systemd_cgroup_v1_dir)
    display.info(f'Container host systemd cgroup directory: {directory}', verbosity=3)

    if not directory:
        cgroup_v1 = SystemdControlGroupV1Status.DIRECTORY_NOT_FOUND
    elif not mount:
        cgroup_v1 = SystemdControlGroupV1Status.FILESYSTEM_NOT_MOUNTED
    elif mount[2] != systemd_cgroup_v1_type:
        cgroup_v1 = SystemdControlGroupV1Status.MOUNT_TYPE_NOT_CORRECT
    elif directory[2:4] != ['0', '0']:
        cgroup_v1 = SystemdControlGroupV1Status.OWNERSHIP_NOT_CORRECT
    else:
        cgroup_v1 = SystemdControlGroupV1Status.VALID

    detect_host_systemd_cgroup_v1.cgroup_v1 = cgroup_v1  # type: ignore[attr-defined]

    return cgroup_v1


@mutex
def detect_host_audit_status(args: EnvironmentConfig) -> int:
    """
    Return the errno result from attempting to query the container host's audit status.

    The following error codes are known to occur:

    EPERM (1) - Operation not permitted
    This occurs when the root user runs a container but lacks the AUDIT_WRITE capability.
    This will cause patched versions of OpenSSH to disconnect after a login succeeds.
    See: https://src.fedoraproject.org/rpms/openssh/blob/f36/f/openssh-7.6p1-audit.patch

    EBADF (9) - Bad file number
    This occurs when the host doesn't support the audit system (the open_audit call fails).
    This allows SSH logins to succeed despite the failure.
    See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/netlink.c#L204-L209

    ECONNREFUSED (111) - Connection refused
    This occurs when a non-root user runs a container without the AUDIT_WRITE capability.
    When sending an audit message, libaudit ignores this error condition.
    This allows SSH logins to succeed despite the failure.
    See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/deprecated.c#L48-L52
    """
    try:
        return detect_host_audit_status.status  # type: ignore[attr-defined]
    except AttributeError:
        pass

    cmd = ['audit-status']
    stdout = run_utility_container(args, f'ansible-test-audit-{args.session_name}', cmd)
    status = detect_host_audit_status.status = int(stdout) * -1  # type: ignore[attr-defined]
    name = errno.errorcode.get(status, '?')

    display.info(f'Container host audit status: {name} ({status})', verbosity=1)

    return status


@mutex
def detect_container_loginuid(args: EnvironmentConfig) -> int | None:
    """Return the loginuid used by the container host to run containers, or None if the audit subsystem is unavailable."""
    try:
        return detect_container_loginuid.loginuid  # type: ignore[attr-defined]
    except AttributeError:
        pass

    cmd = ['sh', '-c', 'cat /proc/self/loginuid || true']
    stdout = run_utility_container(args, f'ansible-test-loginuid-{args.session_name}', cmd=cmd)
    loginuid = int(stdout) if stdout else None

    display.info(f'Container loginuid: {loginuid if loginuid is not None else "unavailable"}', verbosity=1)

    detect_container_loginuid.loginuid = loginuid  # type: ignore[attr-defined]

    return loginuid


@mutex
def detect_container_max_num_open_files(args: EnvironmentConfig) -> int:
    """Return the max number of open files supported by the container host to run containers."""
    try:
        return detect_container_max_num_open_files.hard_limit  # type: ignore[attr-defined]
    except AttributeError:
        pass

    cmd = ['sh', '-c', 'cat /proc/sys/fs/nr_open && ulimit -Hn']
    stdout = run_utility_container(args, f'ansible-test-ulimit-{args.session_name}', cmd=cmd)
    lines = stdout.splitlines()
    system_limit, hard_limit = int(lines[0]), int(lines[1])

    if hard_limit < MAX_NUM_OPEN_FILES and hard_limit < system_limit and require_docker().command == 'docker':
        # Podman will use the highest possible limits, up to its default of 1M.
        # See: https://github.com/containers/podman/blob/009afb50b308548eb129bc68e654db6c6ad82e7a/pkg/specgen/generate/oci.go#L39-L58
        # Docker limits are less predictable. They could be the system limit or the user's soft limit.
        # If Docker is running as root it should be able to use the system limit.
        # When Docker reports a limit below the preferred value and the system limit, attempt to use the preferred value, up to the system limit.
        options = ['--ulimit', f'nofile={min(system_limit, MAX_NUM_OPEN_FILES)}']
        cmd = ['sh', '-c', 'ulimit -Hn']

        try:
            stdout = run_utility_container(args, f'ansible-test-ulimit-{args.session_name}', options=options, cmd=cmd)
        except SubprocessError as ex:
            display.warning(str(ex))
        else:
            hard_limit = int(stdout)

    display.info(f'Container host max open files: {hard_limit}', verbosity=1)

    if hard_limit < MAX_NUM_OPEN_FILES:
        display.warning(f'Unable to set container max open files to {MAX_NUM_OPEN_FILES}. Using container host limit of {hard_limit} instead.')

    detect_container_max_num_open_files.hard_limit = hard_limit  # type: ignore[attr-defined]

    return hard_limit


def run_utility_container(args: EnvironmentConfig, name: str, cmd: list[str], options: list[str] | None = None, remove: bool = True) -> str:
    """Run the specified command using the ansible-test utility container and return stdout."""
    options = list(options or [])

    if remove:
        options.append('--rm')

    docker_pull(args, UTILITY_IMAGE)

    return docker_run(args, UTILITY_IMAGE, name, options=options, cmd=cmd)


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
                version = raw_command([command, '-v'], capture=True)[0].strip()

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
        stdout = raw_command(['podman', 'system', 'connection', 'list', '--format=json'], capture=True)[0]
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
    path = '/proc/self/cpuset'
    container_id = None

    if os.path.exists(path):
        # File content varies based on the environment:
        #   No Container: /
        #   Docker: /docker/c86f3732b5ba3d28bb83b6e14af767ab96abbc52de31313dcb1176a62d91a507
        #   Azure Pipelines (Docker): /azpl_job/0f2edfed602dd6ec9f2e42c867f4d5ee640ebf4c058e6d3196d4393bb8fd0891
        #   Podman: /../../../../../..
        contents = read_text_file(path)

        cgroup_path, cgroup_name = os.path.split(contents.strip())

        if cgroup_path in ('/docker', '/azpl_job'):
            container_id = cgroup_name

    if container_id:
        display.info('Detected execution in Docker container: %s' % container_id, verbosity=1)

    return container_id


@mutex
def get_docker_preferred_network_name(args: EnvironmentConfig) -> str | None:
    """
    Return the preferred network name for use with Docker. The selection logic is:
    - the network selected by the user with `--docker-network`
    - the network of the currently running docker container (if any)
    - the default docker network (returns None)
    """
    try:
        return get_docker_preferred_network_name.network  # type: ignore[attr-defined]
    except AttributeError:
        pass

    network = None

    if args.docker_network:
        network = args.docker_network
    else:
        current_container_id = get_docker_container_id()

        if current_container_id:
            # Make sure any additional containers we launch use the same network as the current container we're running in.
            # This is needed when ansible-test is running in a container that is not connected to Docker's default network.
            container = docker_inspect(args, current_container_id, always=True)
            network = container.get_network_name()

    # The default docker behavior puts containers on the same network.
    # The default podman behavior puts containers on isolated networks which don't allow communication between containers or network disconnect.
    # Starting with podman version 2.1.0 rootless containers are able to join networks.
    # Starting with podman version 2.2.0 containers can be disconnected from networks.
    # To maintain feature parity with docker, detect and use the default "podman" network when running under podman.
    if network is None and require_docker().command == 'podman' and docker_network_inspect(args, 'podman', always=True):
        network = 'podman'

    get_docker_preferred_network_name.network = network  # type: ignore[attr-defined]

    return network


def is_docker_user_defined_network(network: str) -> bool:
    """Return True if the network being used is a user-defined network."""
    return bool(network) and network != 'bridge'


def docker_pull(args: EnvironmentConfig, image: str) -> None:
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


def __docker_pull(args: EnvironmentConfig, image: str) -> None:
    """Internal implementation for docker_pull. Do not call directly."""
    inspect: DockerImageInspect | None = None

    if '@' not in image and ':' not in image:
        display.info('Skipping pull of image without tag or digest: %s' % image, verbosity=2)
    elif inspect := docker_image_inspect(args, image, always=True):
        display.info('Skipping pull of existing image: %s' % image, verbosity=2)
    else:
        for _iteration in range(1, 10):
            try:
                docker_command(args, ['pull', image], capture=False)
                break
            except SubprocessError:
                display.warning('Failed to pull docker image "%s". Waiting a few seconds before trying again.' % image)
                time.sleep(3)
        else:
            raise ApplicationError('Failed to pull docker image "%s".' % image)

    if not inspect:
        inspect = docker_image_inspect(args, image)

    if args.explain:
        return

    if not inspect:
        raise ApplicationError(f'Image "{image}" not found after pull completed.')

    if inspect.volumes:
        display.warning(f'Image "{image}" contains {len(inspect.volumes)} volume(s): {", ".join(sorted(inspect.volumes))}\n'
                        'This may result in leaking anonymous volumes. It may also prevent the image from working on some hosts or container engines.\n'
                        'The image should be rebuilt without the use of the VOLUME instruction.',
                        unique=True)


def docker_cp_to(args: EnvironmentConfig, container_id: str, src: str, dst: str) -> None:
    """Copy a file to the specified container."""
    docker_command(args, ['cp', src, '%s:%s' % (container_id, dst)], capture=True)


def docker_run(
        args: EnvironmentConfig,
        image: str,
        name: str,
        options: t.Optional[list[str]],
        cmd: t.Optional[list[str]] = None,
        create_only: bool = False,
) -> str:
    """Run a container using the given docker image."""
    options = list(options or [])
    options.extend(['--name', name])

    if not cmd:
        cmd = []

    if create_only:
        command = 'create'
    else:
        command = 'run'

    network = get_docker_preferred_network_name(args)

    if is_docker_user_defined_network(network):
        # Only when the network is not the default bridge network.
        options.extend(['--network', network])

    for _iteration in range(1, 3):
        try:
            stdout = docker_command(args, [command] + options + [image] + cmd, capture=True)[0]

            if args.explain:
                return ''.join(random.choice('0123456789abcdef') for _iteration in range(64))

            return stdout.strip()
        except SubprocessError as ex:
            display.error(ex.message)
            display.warning('Failed to run docker image "%s". Waiting a few seconds before trying again.' % image)
            docker_rm(args, name)  # podman doesn't remove containers after create if run fails
            time.sleep(3)

    raise ApplicationError('Failed to run docker image "%s".' % image)


def docker_start(args: EnvironmentConfig, container_id: str, options: t.Optional[list[str]] = None) -> tuple[t.Optional[str], t.Optional[str]]:
    """
    Start a docker container by name or ID
    """
    if not options:
        options = []

    for _iteration in range(1, 3):
        try:
            return docker_command(args, ['start'] + options + [container_id], capture=True)
        except SubprocessError as ex:
            display.error(ex.message)
            display.warning('Failed to start docker container "%s". Waiting a few seconds before trying again.' % container_id)
            time.sleep(3)

    raise ApplicationError('Failed to run docker container "%s".' % container_id)


def docker_rm(args: EnvironmentConfig, container_id: str) -> None:
    """Remove the specified container."""
    try:
        docker_command(args, ['rm', '-f', container_id], capture=True)
    except SubprocessError as ex:
        if 'no such container' in ex.stderr:
            pass  # podman does not handle this gracefully, exits 1
        else:
            raise ex


class DockerError(Exception):
    """General Docker error."""


class ContainerNotFoundError(DockerError):
    """The container identified by `identifier` was not found."""
    def __init__(self, identifier):
        super().__init__('The container "%s" was not found.' % identifier)

        self.identifier = identifier


class DockerInspect:
    """The results of `docker inspect` for a single container."""
    def __init__(self, args: EnvironmentConfig, inspection: dict[str, t.Any]) -> None:
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

    def get_ip_address(self) -> t.Optional[str]:
        """Return the IP address of the container for the preferred docker network."""
        if self.networks:
            network_name = get_docker_preferred_network_name(self.args)

            if not network_name:
                # Sort networks and use the first available.
                # This assumes all containers will have access to the same networks.
                network_name = sorted(self.networks.keys()).pop(0)

            ipaddress = self.networks[network_name]['IPAddress']
        else:
            ipaddress = self.network_settings['IPAddress']

        if not ipaddress:
            return None

        return ipaddress


def docker_inspect(args: EnvironmentConfig, identifier: str, always: bool = False) -> DockerInspect:
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


def docker_network_disconnect(args: EnvironmentConfig, container_id: str, network: str) -> None:
    """Disconnect the specified docker container from the given network."""
    docker_command(args, ['network', 'disconnect', network, container_id], capture=True)


class DockerImageInspect:
    """The results of `docker image inspect` for a single image."""
    def __init__(self, args: EnvironmentConfig, inspection: dict[str, t.Any]) -> None:
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


def docker_image_inspect(args: EnvironmentConfig, image: str, always: bool = False) -> DockerImageInspect | None:
    """
    Return the results of `docker image inspect` for the specified image or None if the image does not exist.
    """
    try:
        stdout = docker_command(args, ['image', 'inspect', image], capture=True, always=always)[0]
    except SubprocessError:
        stdout = '[]'

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) == 1:
        return DockerImageInspect(args, items[0])

    return None


class DockerNetworkInspect:
    """The results of `docker network inspect` for a single network."""
    def __init__(self, args: EnvironmentConfig, inspection: dict[str, t.Any]) -> None:
        self.args = args
        self.inspection = inspection


def docker_network_inspect(args: EnvironmentConfig, network: str, always: bool = False) -> DockerNetworkInspect | None:
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


def docker_logs(args: EnvironmentConfig, container_id: str) -> None:
    """Display logs for the specified container. If an error occurs, it is displayed rather than raising an exception."""
    try:
        docker_command(args, ['logs', container_id], capture=False)
    except SubprocessError as ex:
        display.error(str(ex))


def docker_exec(
        args: EnvironmentConfig,
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

    return docker_command(args, ['exec'] + options + [container_id] + cmd, capture=capture, stdin=stdin, stdout=stdout, interactive=interactive,
                          output_stream=output_stream, data=data)


def docker_info(args: CommonConfig) -> dict[str, t.Any]:
    """Return a dictionary containing details from the `docker info` command."""
    stdout, _dummy = docker_command(args, ['info', '--format', '{{json .}}'], capture=True, always=True)
    return json.loads(stdout)


def docker_version(args: CommonConfig) -> dict[str, t.Any]:
    """Return a dictionary containing details from the `docker version` command."""
    stdout, _dummy = docker_command(args, ['version', '--format', '{{json .}}'], capture=True, always=True)
    return json.loads(stdout)


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

    return run_command(args, command + cmd, env=env, capture=capture, stdin=stdin, stdout=stdout, interactive=interactive, always=always,
                       output_stream=output_stream, data=data)


def docker_environment() -> dict[str, str]:
    """Return a dictionary of docker related environment variables found in the current environment."""
    env = common_environment()
    env.update(dict((key, os.environ[key]) for key in os.environ if key.startswith('DOCKER_') or key.startswith('CONTAINER_')))
    return env
