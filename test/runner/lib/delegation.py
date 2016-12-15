"""Delegate test execution to another environment."""

from __future__ import absolute_import, print_function

import os
import sys
import time

import lib.pytar
import lib.thread

from lib.executor import (
    SUPPORTED_PYTHON_VERSIONS,
    EnvironmentConfig,
    IntegrationConfig,
    SubprocessError,
    ShellConfig,
    TestConfig,
    create_shell_command,
)

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.manage_ci import (
    ManagePosixCI,
)

from lib.util import (
    ApplicationError,
    run_command,
    display,
)

BUFFER_SIZE = 256 * 256


def delegate(args, exclude, require):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
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

    if not args.explain:
        lib.pytar.create_tarfile('/tmp/ansible.tgz', '.', lib.pytar.ignore)

    try:
        if util_image:
            util_id, _ = run_command(args, [
                'docker', 'run', '--detach',
                util_image,
            ], capture=True)

            if args.explain:
                util_id = 'util_id'
            else:
                util_id = util_id.strip()
        else:
            util_id = None

        test_cmd = [
            'docker', 'run', '--detach',
            '--volume', '/sys/fs/cgroup:/sys/fs/cgroup:ro',
            '--privileged=%s' % str(privileged).lower(),
        ]

        if util_id:
            test_cmd += [
                '--link', '%s:ansible.http.tests' % util_id,
                '--link', '%s:sni1.ansible.http.tests' % util_id,
                '--link', '%s:sni2.ansible.http.tests' % util_id,
                '--link', '%s:fail.ansible.http.tests' % util_id,
                '--env', 'HTTPTESTER=1',
            ]

        test_id, _ = run_command(args, test_cmd + [test_image], capture=True)

        if args.explain:
            test_id = 'test_id'
        else:
            test_id = test_id.strip()

        # write temporary files to /root since /tmp isn't ready immediately on container start
        docker_put(args, test_id, 'test/runner/setup/docker.sh', '/root/docker.sh')

        run_command(args,
                    ['docker', 'exec', test_id, '/bin/bash', '/root/docker.sh'])

        docker_put(args, test_id, '/tmp/ansible.tgz', '/root/ansible.tgz')

        run_command(args,
                    ['docker', 'exec', test_id, 'mkdir', '/root/ansible'])

        run_command(args,
                    ['docker', 'exec', test_id, 'tar', 'oxzf', '/root/ansible.tgz', '--directory', '/root/ansible'])

        try:
            command = ['docker', 'exec']

            if isinstance(args, ShellConfig):
                command.append('-it')

            run_command(args, command + [test_id] + cmd)
        finally:
            run_command(args,
                        ['docker', 'exec', test_id,
                         'tar', 'czf', '/root/results.tgz', '--directory', '/root/ansible/test', 'results'])

            docker_get(args, test_id, '/root/results.tgz', '/tmp/results.tgz')

            run_command(args,
                        ['tar', 'oxzf', '/tmp/results.tgz', '-C', 'test'])
    finally:
        if util_id:
            run_command(args,
                        ['docker', 'rm', '-f', util_id],
                        capture=True)

        if test_id:
            run_command(args,
                        ['docker', 'rm', '-f', test_id],
                        capture=True)


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
            run_command(args, ['docker', 'pull', image])
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
    cmd = ['docker', 'exec', '-i', container_id, 'dd', 'of=%s' % dst, 'bs=%s' % BUFFER_SIZE]

    with open(src, 'rb') as src_fd:
        run_command(args, cmd, stdin=src_fd, capture=True)


def docker_get(args, container_id, src, dst):
    """
    :type args: EnvironmentConfig
    :type container_id: str
    :type src: str
    :type dst: str
    """
    # avoid 'docker cp' due to a bug which causes 'docker rm' to fail
    cmd = ['docker', 'exec', '-i', container_id, 'dd', 'if=%s' % src, 'bs=%s' % BUFFER_SIZE]

    with open(dst, 'wb') as dst_fd:
        run_command(args, cmd, stdout=dst_fd, capture=True)


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
    :return: list[str]
    """
    options['--color'] = 1

    cmd = [path]
    cmd += list(filter_options(args, sys.argv[1:], options, exclude, require))
    cmd += ['--color', 'yes' if args.color else 'no']

    if args.requirements:
        cmd += ['--requirements']

    if isinstance(args, ShellConfig):
        cmd = create_shell_command(cmd)

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
