"""Functions for accessing docker via the docker cli."""

from __future__ import absolute_import, print_function

import json
import os
import time

from lib.executor import (
    SubprocessError,
)

from lib.util import (
    ApplicationError,
    run_command,
    common_environment,
    display,
    find_executable,
)

from lib.config import (
    EnvironmentConfig,
)

BUFFER_SIZE = 256 * 256


def docker_available():
    """
    :rtype: bool
    """
    return find_executable('docker', required=False)


def get_docker_container_id():
    """
    :rtype: str | None
    """
    path = '/proc/self/cgroup'

    if not os.path.exists(path):
        return None

    with open(path) as cgroup_fd:
        contents = cgroup_fd.read()

    paths = [line.split(':')[2] for line in contents.splitlines()]
    container_ids = set(path.split('/')[2] for path in paths if path.startswith('/docker/'))

    if not container_ids:
        return None

    if len(container_ids) == 1:
        return container_ids.pop()

    raise ApplicationError('Found multiple container_id candidates: %s\n%s' % (sorted(container_ids), contents))


def get_docker_container_ip(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :rtype: str
    """
    results = docker_inspect(args, container_id)
    ipaddress = results[0]['NetworkSettings']['IPAddress']
    return ipaddress


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

    for _ in range(1, 10):
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

    for _ in range(1, 3):
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
    stdout, _dummy = docker_command(args, ['images', image, '--format', '{{json .}}'], capture=True, always=True)
    results = [json.loads(line) for line in stdout.splitlines()]
    return results


def docker_rm(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    """
    docker_command(args, ['rm', '-f', container_id], capture=True)


def docker_inspect(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :rtype: list[dict]
    """
    if args.explain:
        return []

    try:
        stdout, _ = docker_command(args, ['inspect', container_id], capture=True)
        return json.loads(stdout)
    except SubprocessError as ex:
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
        stdout, _ = docker_command(args, ['network', 'inspect', network], capture=True)
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
    :type stdin: file | None
    :type stdout: file | None
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
