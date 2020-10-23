"""Functions for accessing docker via the docker cli."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import time

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
)

from .config import (
    EnvironmentConfig,
)

BUFFER_SIZE = 256 * 256


def docker_available():
    """
    :rtype: bool
    """
    return find_executable('docker', required=False)


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
        with open(path) as cgroup_fd:
            contents = cgroup_fd.read()

        cgroup_path, cgroup_name = os.path.split(contents.strip())

        if cgroup_path in ('/docker', '/azpl_job'):
            container_id = cgroup_name

    get_docker_container_id.container_id = container_id

    if container_id:
        display.info('Detected execution in Docker container: %s' % container_id, verbosity=1)

    return container_id


def get_docker_container_ip(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :rtype: str
    """
    results = docker_inspect(args, container_id)
    network_settings = results[0]['NetworkSettings']
    networks = network_settings.get('Networks')

    if networks:
        network_name = get_docker_preferred_network_name(args)
        ipaddress = networks[network_name]['IPAddress']
    else:
        # podman doesn't provide Networks, fall back to using IPAddress
        ipaddress = network_settings['IPAddress']

    if not ipaddress:
        raise ApplicationError('Cannot retrieve IP address for container: %s' % container_id)

    return ipaddress


def get_docker_network_name(args, container_id):  # type: (EnvironmentConfig, str) -> str
    """
    Return the network name of the specified container.
    Raises an exception if zero or more than one network is found.
    """
    networks = get_docker_networks(args, container_id)

    if not networks:
        raise ApplicationError('No network found for Docker container: %s.' % container_id)

    if len(networks) > 1:
        raise ApplicationError('Found multiple networks for Docker container %s instead of only one: %s' % (container_id, ', '.join(networks)))

    return networks[0]


def get_docker_preferred_network_name(args):  # type: (EnvironmentConfig) -> str
    """
    Return the preferred network name for use with Docker. The selection logic is:
    - the network selected by the user with `--docker-network`
    - the network of the currently running docker container (if any)
    - the default docker network (returns None)
    """
    network = None

    if args.docker_network:
        network = args.docker_network
    else:
        current_container_id = get_docker_container_id()

        if current_container_id:
            # Make sure any additional containers we launch use the same network as the current container we're running in.
            # This is needed when ansible-test is running in a container that is not connected to Docker's default network.
            network = get_docker_network_name(args, current_container_id)

    return network


def is_docker_user_defined_network(network):  # type: (str) -> bool
    """Return True if the network being used is a user-defined network."""
    return network and network != 'bridge'


def get_docker_networks(args, container_id):
    """
    :param args: EnvironmentConfig
    :param container_id: str
    :rtype: list[str]
    """
    results = docker_inspect(args, container_id)
    networks = sorted(results[0]['NetworkSettings']['Networks'])
    return networks


def docker_pull(args, image):
    """
    :type args: EnvironmentConfig
    :type image: str
    """
    if ('@' in image or ':' in image) and docker_images(args, image):
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


def docker_put(args, container_id, src, dst):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type src: str
    :type dst: str
    """
    # avoid 'docker cp' due to a bug which causes 'docker rm' to fail
    with open(src, 'rb') as src_fd:
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
    with open(dst, 'wb') as dst_fd:
        docker_exec(args, container_id, ['dd', 'if=%s' % src, 'bs=%s' % BUFFER_SIZE],
                    options=['-i'], stdout=dst_fd, capture=True)


def docker_run(args, image, options, cmd=None):
    """
    :type args: EnvironmentConfig
    :type image: str
    :type options: list[str] | None
    :type cmd: list[str] | None
    :rtype: str | None, str | None
    """
    if not options:
        options = []

    if not cmd:
        cmd = []

    network = get_docker_preferred_network_name(args)

    if is_docker_user_defined_network(network):
        # Only when the network is not the default bridge network.
        # Using this with the default bridge network results in an error when using --link: links are only supported for user-defined networks
        options.extend(['--network', network])

    for _iteration in range(1, 3):
        try:
            return docker_command(args, ['run'] + options + [image] + cmd, capture=True)
        except SubprocessError as ex:
            display.error(ex)
            display.warning('Failed to run docker image "%s". Waiting a few seconds before trying again.' % image)
            time.sleep(3)

    raise ApplicationError('Failed to run docker image "%s".' % image)


def docker_images(args, image):
    """
    :param args: CommonConfig
    :param image: str
    :rtype: list[dict[str, any]]
    """
    try:
        stdout, _dummy = docker_command(args, ['images', image, '--format', '{{json .}}'], capture=True, always=True)
    except SubprocessError as ex:
        if 'no such image' in ex.stderr:
            stdout = ''  # podman does not handle this gracefully, exits 125
        else:
            raise ex
    results = [json.loads(line) for line in stdout.splitlines()]
    return results


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


def docker_inspect(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :rtype: list[dict]
    """
    if args.explain:
        return []

    try:
        stdout = docker_command(args, ['inspect', container_id], capture=True)[0]
        return json.loads(stdout)
    except SubprocessError as ex:
        if 'no such image' in ex.stderr:
            return []  # podman does not handle this gracefully, exits 125
        try:
            return json.loads(ex.stdout)
        except Exception:
            raise ex


def docker_network_disconnect(args, container_id, network):
    """
    :param args: EnvironmentConfig
    :param container_id: str
    :param network: str
    """
    docker_command(args, ['network', 'disconnect', network, container_id], capture=True)


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


def docker_exec(args, container_id, cmd, options=None, capture=False, stdin=None, stdout=None):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type cmd: list[str]
    :type options: list[str] | None
    :type capture: bool
    :type stdin: BinaryIO | None
    :type stdout: BinaryIO | None
    :rtype: str | None, str | None
    """
    if not options:
        options = []

    return docker_command(args, ['exec'] + options + [container_id] + cmd, capture=capture, stdin=stdin, stdout=stdout)


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


def docker_command(args, cmd, capture=False, stdin=None, stdout=None, always=False):
    """
    :type args: CommonConfig
    :type cmd: list[str]
    :type capture: bool
    :type stdin: file | None
    :type stdout: file | None
    :type always: bool
    :rtype: str | None, str | None
    """
    env = docker_environment()
    return run_command(args, ['docker'] + cmd, env=env, capture=capture, stdin=stdin, stdout=stdout, always=always)


def docker_environment():
    """
    :rtype: dict[str, str]
    """
    env = common_environment()
    env.update(dict((key, os.environ[key]) for key in os.environ if key.startswith('DOCKER_')))
    return env
