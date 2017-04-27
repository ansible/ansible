"""Delegate test execution to another environment."""

from __future__ import absolute_import, print_function

import os
import sys
import tempfile
import time

import lib.pytar
import lib.thread

from lib.executor import (
    SUPPORTED_PYTHON_VERSIONS,
    IntegrationConfig,
    SubprocessError,
    ShellConfig,
    SanityConfig,
    UnitsConfig,
    create_shell_command,
)

from lib.test import (
    TestConfig,
)

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.manage_ci import (
    ManagePosixCI,
)

from lib.util import (
    ApplicationError,
    EnvironmentConfig,
    run_command,
    common_environment,
    display,
)

BUFFER_SIZE = 256 * 256


def delegate(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :rtype: bool
    """
    if isinstance(args, TestConfig):
        with tempfile.NamedTemporaryFile(prefix='metadata-', suffix='.json', dir=os.getcwd()) as metadata_fd:
            args.metadata_path = os.path.basename(metadata_fd.name)
            args.metadata.to_file(args.metadata_path)

            try:
                return delegate_command(args, exclude, require)
            finally:
                args.metadata_path = None
    else:
        return delegate_command(args, exclude, require)


def delegate_command(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :rtype: bool
    """
    if args.tox:
        delegate_tox(args, exclude, require)
        return True

    if args.docker:
        delegate_docker(args, exclude, require)
        return True

    if args.remote:
        delegate_remote(args, exclude, require)
        return True

    return False


def delegate_tox(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    """
    if args.python:
        versions = args.python,

        if args.python not in SUPPORTED_PYTHON_VERSIONS:
            raise ApplicationError('tox does not support Python version %s' % args.python)
    else:
        versions = SUPPORTED_PYTHON_VERSIONS

    options = {
        '--tox': args.tox_args,
        '--tox-sitepackages': 0,
    }

    for version in versions:
        tox = ['tox', '-c', 'test/runner/tox.ini', '-e', 'py' + version.replace('.', '')]

        if args.tox_sitepackages:
            tox.append('--sitepackages')

        tox.append('--')

        cmd = generate_command(args, os.path.abspath('test/runner/test.py'), options, exclude, require)

        if not args.python:
            cmd += ['--python', version]

        run_command(args, tox + cmd)


def delegate_docker(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    """
    util_image = args.docker_util
    test_image = args.docker
    privileged = args.docker_privileged

    if util_image:
        docker_pull(args, util_image)

    docker_pull(args, test_image)

    util_id = None
    test_id = None

    options = {
        '--docker': 1,
        '--docker-privileged': 0,
        '--docker-util': 1,
    }

    cmd = generate_command(args, '/root/ansible/test/runner/test.py', options, exclude, require)

    if isinstance(args, IntegrationConfig):
        if not args.allow_destructive:
            cmd.append('--allow-destructive')

    cmd_options = []

    if isinstance(args, ShellConfig):
        cmd_options.append('-it')

    if not args.explain:
        lib.pytar.create_tarfile('/tmp/ansible.tgz', '.', lib.pytar.ignore)

    try:
        if util_image:
            util_options = [
                '--detach',
            ]

            util_id, _ = docker_run(args, util_image, options=util_options)

            if args.explain:
                util_id = 'util_id'
            else:
                util_id = util_id.strip()
        else:
            util_id = None

        test_options = [
            '--detach',
            '--volume', '/sys/fs/cgroup:/sys/fs/cgroup:ro',
            '--privileged=%s' % str(privileged).lower(),
        ]

        if util_id:
            test_options += [
                '--link', '%s:ansible.http.tests' % util_id,
                '--link', '%s:sni1.ansible.http.tests' % util_id,
                '--link', '%s:sni2.ansible.http.tests' % util_id,
                '--link', '%s:fail.ansible.http.tests' % util_id,
                '--env', 'HTTPTESTER=1',
            ]

        test_id, _ = docker_run(args, test_image, options=test_options)

        if args.explain:
            test_id = 'test_id'
        else:
            test_id = test_id.strip()

        # write temporary files to /root since /tmp isn't ready immediately on container start
        docker_put(args, test_id, 'test/runner/setup/docker.sh', '/root/docker.sh')
        docker_exec(args, test_id, ['/bin/bash', '/root/docker.sh'])
        docker_put(args, test_id, '/tmp/ansible.tgz', '/root/ansible.tgz')
        docker_exec(args, test_id, ['mkdir', '/root/ansible'])
        docker_exec(args, test_id, ['tar', 'oxzf', '/root/ansible.tgz', '-C', '/root/ansible'])

        # docker images are only expected to have a single python version available
        if isinstance(args, UnitsConfig) and not args.python:
            cmd += ['--python', 'default']

        try:
            docker_exec(args, test_id, cmd, options=cmd_options)
        finally:
            docker_exec(args, test_id, ['tar', 'czf', '/root/results.tgz', '-C', '/root/ansible/test', 'results'])
            docker_get(args, test_id, '/root/results.tgz', '/tmp/results.tgz')
            run_command(args, ['tar', 'oxzf', '/tmp/results.tgz', '-C', 'test'])
    finally:
        if util_id:
            docker_rm(args, util_id)

        if test_id:
            docker_rm(args, test_id)


def docker_pull(args, image):
    """
    :type args: EnvironmentConfig
    :type image: str
    """
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


def docker_run(args, image, options):
    """
    :type args: EnvironmentConfig
    :type image: str
    :type options: list[str] | None
    :rtype: str | None, str | None
    """
    if not options:
        options = []

    for _ in range(1, 3):
        try:
            return docker_command(args, ['run'] + options + [image], capture=True)
        except SubprocessError as ex:
            display.error(ex)
            display.warning('Failed to run docker image "%s". Waiting a few seconds before trying again.' % image)
            time.sleep(3)

    raise ApplicationError('Failed to run docker image "%s".' % image)


def docker_rm(args, container_id):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    """
    docker_command(args, ['rm', '-f', container_id], capture=True)


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


def docker_command(args, cmd, capture=False, stdin=None, stdout=None):
    """
    :type args: EnvironmentConfig
    :type cmd: list[str]
    :type capture: bool
    :type stdin: file | None
    :type stdout: file | None
    :rtype: str | None, str | None
    """
    env = docker_environment()
    return run_command(args, ['docker'] + cmd, env=env, capture=capture, stdin=stdin, stdout=stdout)


def docker_environment():
    """
    :rtype: dict[str, str]
    """
    env = common_environment()
    env.update(dict((key, os.environ[key]) for key in os.environ if key.startswith('DOCKER_')))
    return env


def delegate_remote(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    """
    parts = args.remote.split('/', 1)

    platform = parts[0]
    version = parts[1]

    core_ci = AnsibleCoreCI(args, platform, version, stage=args.remote_stage)

    try:
        core_ci.start()
        core_ci.wait()

        options = {
            '--remote': 1,
        }

        cmd = generate_command(args, 'ansible/test/runner/test.py', options, exclude, require)

        if isinstance(args, IntegrationConfig):
            if not args.allow_destructive:
                cmd.append('--allow-destructive')

        # remote instances are only expected to have a single python version available
        if isinstance(args, UnitsConfig) and not args.python:
            cmd += ['--python', 'default']

        manage = ManagePosixCI(core_ci)
        manage.setup()

        try:
            manage.ssh(cmd)
        finally:
            manage.ssh('rm -rf /tmp/results && cp -a ansible/test/results /tmp/results')
            manage.download('/tmp/results', 'test')
    finally:
        pass


def generate_command(args, path, options, exclude, require):
    """
    :type args: EnvironmentConfig
    :type path: str
    :type options: dict[str, int]
    :type exclude: list[str]
    :type require: list[str]
    :rtype: list[str]
    """
    options['--color'] = 1

    cmd = [path]
    cmd += list(filter_options(args, sys.argv[1:], options, exclude, require))
    cmd += ['--color', 'yes' if args.color else 'no']

    if args.requirements:
        cmd += ['--requirements']

    if isinstance(args, ShellConfig):
        cmd = create_shell_command(cmd)
    elif isinstance(args, SanityConfig):
        if args.base_branch:
            cmd += ['--base-branch', args.base_branch]

    return cmd


def filter_options(args, argv, options, exclude, require):
    """
    :type args: EnvironmentConfig
    :type argv: list[str]
    :type options: dict[str, int]
    :type exclude: list[str]
    :type require: list[str]
    :rtype: collections.Iterable[str]
    """
    options = options.copy()

    options['--requirements'] = 0

    if isinstance(args, TestConfig):
        options.update({
            '--changed': 0,
            '--tracked': 0,
            '--untracked': 0,
            '--ignore-committed': 0,
            '--ignore-staged': 0,
            '--ignore-unstaged': 0,
            '--changed-from': 1,
            '--changed-path': 1,
            '--metadata': 1,
        })
    elif isinstance(args, SanityConfig):
        options.update({
            '--base-branch': 1,
        })

    remaining = 0

    for arg in argv:
        if not arg.startswith('-') and remaining:
            remaining -= 1
            continue

        remaining = 0

        parts = arg.split('=', 1)
        key = parts[0]

        if key in options:
            remaining = options[key] - len(parts) + 1
            continue

        yield arg

    for target in exclude:
        yield '--exclude'
        yield target

    for target in require:
        yield '--require'
        yield target

    if isinstance(args, TestConfig):
        if args.metadata_path:
            yield '--metadata'
            yield args.metadata_path
