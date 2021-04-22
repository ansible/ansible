"""Functions for accessing docker via the docker cli."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import random
import socket
import time

from . import types as t

from .io import (
    open_binary_file,
    read_text_file,
)

from .util import (
    ApplicationError,
    common_environment,
    display,
    find_executable,
    SubprocessError,
)

from .http import (
    urlparse,
)

from .util_common import (
    run_command,
    raw_command,
)

from .config import (
    EnvironmentConfig,
)

BUFFER_SIZE = 256 * 256

DOCKER_COMMANDS = [
    'docker',
    'podman',
]


class DockerCommand:
    """Details about the available docker command."""
    def __init__(self, command, executable, version):  # type: (str, str, str) -> None
        self.command = command
        self.executable = executable
        self.version = version

    @staticmethod
    def detect():  # type: () -> t.Optional[DockerCommand]
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


def get_docker_command(required=False):  # type: (bool) -> t.Optional[DockerCommand]
    """Return the docker command to invoke. Raises an exception if docker is not available."""
    try:
        return get_docker_command.cmd
    except AttributeError:
        get_docker_command.cmd = DockerCommand.detect()

    if required and not get_docker_command.cmd:
        raise ApplicationError("No container runtime detected. Supported commands: %s" % ', '.join(DOCKER_COMMANDS))

    return get_docker_command.cmd


def get_docker_host_ip():  # type: () -> str
    """Return the IP of the Docker host."""
    try:
        return get_docker_host_ip.ip
    except AttributeError:
        pass

    docker_host_ip = get_docker_host_ip.ip = socket.gethostbyname(get_docker_hostname())

    display.info('Detected docker host IP: %s' % docker_host_ip, verbosity=1)

    return docker_host_ip


def get_docker_hostname():  # type: () -> str
    """Return the hostname of the Docker service."""
    try:
        return get_docker_hostname.hostname
    except AttributeError:
        pass

    docker_host = os.environ.get('DOCKER_HOST')

    if docker_host and docker_host.startswith('tcp://'):
        try:
            hostname = urlparse(docker_host)[1].split(':')[0]
            display.info('Detected Docker host: %s' % hostname, verbosity=1)
        except ValueError:
            hostname = 'localhost'
            display.warning('Could not parse DOCKER_HOST environment variable "%s", falling back to localhost.' % docker_host)
    else:
        hostname = 'localhost'
        display.info('Assuming Docker is available on localhost.', verbosity=1)

    get_docker_hostname.hostname = hostname

    return hostname


def get_docker_container_id():
    """
    :rtype: str | None
    """
    try:
        return get_docker_container_id.container_id
    except AttributeError:
        pass

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

    get_docker_container_id.container_id = container_id

    if container_id:
        display.info('Detected execution in Docker container: %s' % container_id, verbosity=1)

    return container_id


def get_docker_preferred_network_name(args):  # type: (EnvironmentConfig) -> str
    """
    Return the preferred network name for use with Docker. The selection logic is:
    - the network selected by the user with `--docker-network`
    - the network of the currently running docker container (if any)
    - the default docker network (returns None)
    """
    try:
        return get_docker_preferred_network_name.network
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

    get_docker_preferred_network_name.network = network

    return network


def is_docker_user_defined_network(network):  # type: (str) -> bool
    """Return True if the network being used is a user-defined network."""
    return network and network != 'bridge'


def docker_pull(args, image):
    """
    :type args: EnvironmentConfig
    :type image: str
    """
    if ('@' in image or ':' in image) and docker_image_exists(args, image):
        display.info('Skipping docker pull of existing image with tag or digest: %s' % image, verbosity=2)
        return

    if not args.docker_pull:
        display.warning('Skipping docker pull for "%s". Image may be out-of-date.' % image)
        return

    for _iteration in range(1, 10):
        try:
            docker_command(args, ['pull', image])
            return
        except SubprocessError:
            display.warning('Failed to pull docker image "%s". Waiting a few seconds before trying again.' % image)
            time.sleep(3)

    raise ApplicationError('Failed to pull docker image "%s".' % image)


def docker_cp_to(args, container_id, src, dst):  # type: (EnvironmentConfig, str, str, str) -> None
    """Copy a file to the specified container."""
    docker_command(args, ['cp', src, '%s:%s' % (container_id, dst)])


def docker_put(args, container_id, src, dst):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type src: str
    :type dst: str
    """
    # avoid 'docker cp' due to a bug which causes 'docker rm' to fail
    with open_binary_file(src) as src_fd:
        docker_exec(args, container_id, ['dd', 'of=%s' % dst, 'bs=%s' % BUFFER_SIZE],
                    options=['-i'], stdin=src_fd, capture=True)


def docker_get(args, container_id, src, dst):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type src: str
    :type dst: str
    """
    # avoid 'docker cp' due to a bug which causes 'docker rm' to fail
    with open_binary_file(dst, 'wb') as dst_fd:
        docker_exec(args, container_id, ['dd', 'if=%s' % src, 'bs=%s' % BUFFER_SIZE],
                    options=['-i'], stdout=dst_fd, capture=True)


def docker_run(args, image, options, cmd=None, create_only=False):
    """
    :type args: EnvironmentConfig
    :type image: str
    :type options: list[str] | None
    :type cmd: list[str] | None
    :type create_only[bool] | False
    :rtype: str
    """
    if not options:
        options = []

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
            display.error(ex)
            display.warning('Failed to run docker image "%s". Waiting a few seconds before trying again.' % image)
            time.sleep(3)

    raise ApplicationError('Failed to run docker image "%s".' % image)


def docker_start(args, container_id, options=None):  # type: (EnvironmentConfig, str, t.Optional[t.List[str]]) -> (t.Optional[str], t.Optional[str])
    """
    Start a docker container by name or ID
    """
    if not options:
        options = []

    for _iteration in range(1, 3):
        try:
            return docker_command(args, ['start'] + options + [container_id], capture=True)
        except SubprocessError as ex:
            display.error(ex)
            display.warning('Failed to start docker container "%s". Waiting a few seconds before trying again.' % container_id)
            time.sleep(3)

    raise ApplicationError('Failed to run docker container "%s".' % container_id)


def docker_rm(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    """
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
        super(ContainerNotFoundError, self).__init__('The container "%s" was not found.' % identifier)

        self.identifier = identifier


class DockerInspect:
    """The results of `docker inspect` for a single container."""
    def __init__(self, args, inspection):  # type: (EnvironmentConfig, t.Dict[str, t.Any]) -> None
        self.args = args
        self.inspection = inspection

    # primary properties

    @property
    def id(self):  # type: () -> str
        """Return the ID of the container."""
        return self.inspection['Id']

    @property
    def network_settings(self):  # type: () -> t.Dict[str, t.Any]
        """Return a dictionary of the container network settings."""
        return self.inspection['NetworkSettings']

    @property
    def state(self):  # type: () -> t.Dict[str, t.Any]
        """Return a dictionary of the container state."""
        return self.inspection['State']

    @property
    def config(self):  # type: () -> t.Dict[str, t.Any]
        """Return a dictionary of the container configuration."""
        return self.inspection['Config']

    # nested properties

    @property
    def ports(self):  # type: () -> t.Dict[str, t.List[t.Dict[str, str]]]
        """Return a dictionary of ports the container has published."""
        return self.network_settings['Ports']

    @property
    def networks(self):  # type: () -> t.Optional[t.Dict[str, t.Dict[str, t.Any]]]
        """Return a dictionary of the networks the container is attached to, or None if running under podman, which does not support networks."""
        return self.network_settings.get('Networks')

    @property
    def running(self):  # type: () -> bool
        """Return True if the container is running, otherwise False."""
        return self.state['Running']

    @property
    def env(self):  # type: () -> t.List[str]
        """Return a list of the environment variables used to create the container."""
        return self.config['Env']

    @property
    def image(self):  # type: () -> str
        """Return the image used to create the container."""
        return self.config['Image']

    # functions

    def env_dict(self):  # type: () -> t.Dict[str, str]
        """Return a dictionary of the environment variables used to create the container."""
        return dict((item[0], item[1]) for item in [e.split('=', 1) for e in self.env])

    def get_tcp_port(self, port):  # type: (int) -> t.Optional[t.List[t.Dict[str, str]]]
        """Return a list of the endpoints published by the container for the specified TCP port, or None if it is not published."""
        return self.ports.get('%d/tcp' % port)

    def get_network_names(self):  # type: () -> t.Optional[t.List[str]]
        """Return a list of the network names the container is attached to."""
        if self.networks is None:
            return None

        return sorted(self.networks)

    def get_network_name(self):  # type: () -> str
        """Return the network name the container is attached to. Raises an exception if no network, or more than one, is attached."""
        networks = self.get_network_names()

        if not networks:
            raise ApplicationError('No network found for Docker container: %s.' % self.id)

        if len(networks) > 1:
            raise ApplicationError('Found multiple networks for Docker container %s instead of only one: %s' % (self.id, ', '.join(networks)))

        return networks[0]

    def get_ip_address(self):  # type: () -> t.Optional[str]
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


def docker_inspect(args, identifier, always=False):  # type: (EnvironmentConfig, str, bool) -> DockerInspect
    """
    Return the results of `docker inspect` for the specified container.
    Raises a ContainerNotFoundError if the container was not found.
    """
    try:
        stdout = docker_command(args, ['inspect', identifier], capture=True, always=always)[0]
    except SubprocessError as ex:
        stdout = ex.stdout

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) == 1:
        return DockerInspect(args, items[0])

    raise ContainerNotFoundError(identifier)


def docker_network_disconnect(args, container_id, network):
    """
    :param args: EnvironmentConfig
    :param container_id: str
    :param network: str
    """
    docker_command(args, ['network', 'disconnect', network, container_id], capture=True)


def docker_image_exists(args, image):  # type: (EnvironmentConfig, str) -> bool
    """Return True if the image exists, otherwise False."""
    try:
        docker_command(args, ['image', 'inspect', image], capture=True)
    except SubprocessError:
        return False

    return True


def docker_network_inspect(args, network):
    """
    :type args: EnvironmentConfig
    :type network: str
    :rtype: list[dict]
    """
    if args.explain:
        return []

    try:
        stdout = docker_command(args, ['network', 'inspect', network], capture=True)[0]
        return json.loads(stdout)
    except SubprocessError as ex:
        try:
            return json.loads(ex.stdout)
        except Exception:
            raise ex


def docker_exec(args, container_id, cmd, options=None, capture=False, stdin=None, stdout=None, data=None):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type cmd: list[str]
    :type options: list[str] | None
    :type capture: bool
    :type stdin: BinaryIO | None
    :type stdout: BinaryIO | None
    :type data: str | None
    :rtype: str | None, str | None
    """
    if not options:
        options = []

    if data:
        options.append('-i')

    return docker_command(args, ['exec'] + options + [container_id] + cmd, capture=capture, stdin=stdin, stdout=stdout, data=data)


def docker_info(args):
    """
    :param args: CommonConfig
    :rtype: dict[str, any]
    """
    stdout, _dummy = docker_command(args, ['info', '--format', '{{json .}}'], capture=True, always=True)
    return json.loads(stdout)


def docker_version(args):
    """
    :param args: CommonConfig
    :rtype: dict[str, any]
    """
    stdout, _dummy = docker_command(args, ['version', '--format', '{{json .}}'], capture=True, always=True)
    return json.loads(stdout)


def docker_command(args, cmd, capture=False, stdin=None, stdout=None, always=False, data=None):
    """
    :type args: CommonConfig
    :type cmd: list[str]
    :type capture: bool
    :type stdin: file | None
    :type stdout: file | None
    :type always: bool
    :type data: str | None
    :rtype: str | None, str | None
    """
    env = docker_environment()
    command = get_docker_command(required=True).command
    return run_command(args, [command] + cmd, env=env, capture=capture, stdin=stdin, stdout=stdout, always=always, data=data)


def docker_environment():
    """
    :rtype: dict[str, str]
    """
    env = common_environment()
    env.update(dict((key, os.environ[key]) for key in os.environ if key.startswith('DOCKER_')))
    return env
