"""Delegate test execution to another environment."""

from __future__ import absolute_import, print_function

import os
import re
import sys
import tempfile

import lib.pytar
import lib.thread

from lib.executor import (
    SUPPORTED_PYTHON_VERSIONS,
    HTTPTESTER_HOSTS,
    create_shell_command,
    run_httptester,
    start_httptester,
)

from lib.config import (
    TestConfig,
    EnvironmentConfig,
    IntegrationConfig,
    ShellConfig,
    SanityConfig,
    UnitsConfig,
)

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.manage_ci import (
    ManagePosixCI,
    ManageWindowsCI,
)

from lib.util import (
    ApplicationError,
    run_command,
    common_environment,
    pass_vars,
    display,
)

from lib.docker_util import (
    docker_exec,
    docker_get,
    docker_pull,
    docker_put,
    docker_rm,
    docker_run,
    docker_available,
    docker_network_disconnect,
    get_docker_networks,
)

from lib.cloud import (
    get_cloud_providers,
)

from lib.target import (
    IntegrationTarget,
)


def delegate(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    :rtype: bool
    """
    if isinstance(args, TestConfig):
        with tempfile.NamedTemporaryFile(prefix='metadata-', suffix='.json', dir=os.getcwd()) as metadata_fd:
            args.metadata_path = os.path.basename(metadata_fd.name)
            args.metadata.to_file(args.metadata_path)

            try:
                return delegate_command(args, exclude, require, integration_targets)
            finally:
                args.metadata_path = None
    else:
        return delegate_command(args, exclude, require, integration_targets)


def delegate_command(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    :rtype: bool
    """
    if args.tox:
        delegate_tox(args, exclude, require, integration_targets)
        return True

    if args.docker:
        delegate_docker(args, exclude, require, integration_targets)
        return True

    if args.remote:
        delegate_remote(args, exclude, require, integration_targets)
        return True

    return False


def delegate_tox(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    """
    if args.python:
        versions = args.python_version,

        if args.python_version not in SUPPORTED_PYTHON_VERSIONS:
            raise ApplicationError('tox does not support Python version %s' % args.python_version)
    else:
        versions = SUPPORTED_PYTHON_VERSIONS

    if args.httptester:
        needs_httptester = sorted(target.name for target in integration_targets if 'needs/httptester/' in target.aliases)

        if needs_httptester:
            display.warning('Use --docker or --remote to enable httptester for tests marked "needs/httptester": %s' % ', '.join(needs_httptester))

    options = {
        '--tox': args.tox_args,
        '--tox-sitepackages': 0,
    }

    for version in versions:
        tox = ['tox', '-c', 'test/runner/tox.ini', '-e', 'py' + version.replace('.', '')]

        if args.tox_sitepackages:
            tox.append('--sitepackages')

        tox.append('--')

        cmd = generate_command(args, os.path.abspath('bin/ansible-test'), options, exclude, require)

        if not args.python:
            cmd += ['--python', version]

        if isinstance(args, TestConfig):
            if args.coverage and not args.coverage_label:
                cmd += ['--coverage-label', 'tox-%s' % version]

        env = common_environment()

        # temporary solution to permit ansible-test delegated to tox to provision remote resources
        optional = (
            'SHIPPABLE',
            'SHIPPABLE_BUILD_ID',
            'SHIPPABLE_JOB_NUMBER',
        )

        env.update(pass_vars(required=[], optional=optional))

        run_command(args, tox + cmd, env=env)


def delegate_docker(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    """
    test_image = args.docker
    privileged = args.docker_privileged

    if isinstance(args, ShellConfig):
        use_httptester = args.httptester
    else:
        use_httptester = args.httptester and any('needs/httptester/' in target.aliases for target in integration_targets)

    if use_httptester:
        docker_pull(args, args.httptester)

    docker_pull(args, test_image)

    httptester_id = None
    test_id = None

    options = {
        '--docker': 1,
        '--docker-privileged': 0,
        '--docker-util': 1,
    }

    cmd = generate_command(args, '/root/ansible/bin/ansible-test', options, exclude, require)

    if isinstance(args, TestConfig):
        if args.coverage and not args.coverage_label:
            image_label = args.docker_raw
            image_label = re.sub('[^a-zA-Z0-9]+', '-', image_label)
            cmd += ['--coverage-label', 'docker-%s' % image_label]

    if isinstance(args, IntegrationConfig):
        if not args.allow_destructive:
            cmd.append('--allow-destructive')

    cmd_options = []

    if isinstance(args, ShellConfig) or (isinstance(args, IntegrationConfig) and args.debug_strategy):
        cmd_options.append('-it')

    with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as local_source_fd:
        try:
            if not args.explain:
                if args.docker_keep_git:
                    tar_filter = lib.pytar.AllowGitTarFilter()
                else:
                    tar_filter = lib.pytar.DefaultTarFilter()

                lib.pytar.create_tarfile(local_source_fd.name, '.', tar_filter)

            if use_httptester:
                httptester_id = run_httptester(args)
            else:
                httptester_id = None

            test_options = [
                '--detach',
                '--volume', '/sys/fs/cgroup:/sys/fs/cgroup:ro',
                '--privileged=%s' % str(privileged).lower(),
            ]

            if args.docker_memory:
                test_options.extend([
                    '--memory=%d' % args.docker_memory,
                    '--memory-swap=%d' % args.docker_memory,
                ])

            docker_socket = '/var/run/docker.sock'

            if args.docker_seccomp != 'default':
                test_options += ['--security-opt', 'seccomp=%s' % args.docker_seccomp]

            if os.path.exists(docker_socket):
                test_options += ['--volume', '%s:%s' % (docker_socket, docker_socket)]

            if httptester_id:
                test_options += ['--env', 'HTTPTESTER=1']

                for host in HTTPTESTER_HOSTS:
                    test_options += ['--link', '%s:%s' % (httptester_id, host)]

            if isinstance(args, IntegrationConfig):
                cloud_platforms = get_cloud_providers(args)

                for cloud_platform in cloud_platforms:
                    test_options += cloud_platform.get_docker_run_options()

            test_id, _ = docker_run(args, test_image, options=test_options)

            if args.explain:
                test_id = 'test_id'
            else:
                test_id = test_id.strip()

            # write temporary files to /root since /tmp isn't ready immediately on container start
            docker_put(args, test_id, 'test/runner/setup/docker.sh', '/root/docker.sh')
            docker_exec(args, test_id, ['/bin/bash', '/root/docker.sh'])
            docker_put(args, test_id, local_source_fd.name, '/root/ansible.tgz')
            docker_exec(args, test_id, ['mkdir', '/root/ansible'])
            docker_exec(args, test_id, ['tar', 'oxzf', '/root/ansible.tgz', '-C', '/root/ansible'])

            # docker images are only expected to have a single python version available
            if isinstance(args, UnitsConfig) and not args.python:
                cmd += ['--python', 'default']

            # run unit tests unprivileged to prevent stray writes to the source tree
            # also disconnect from the network once requirements have been installed
            if isinstance(args, UnitsConfig):
                writable_dirs = [
                    '/root/ansible/.pytest_cache',
                ]

                docker_exec(args, test_id, ['mkdir', '-p'] + writable_dirs)
                docker_exec(args, test_id, ['chmod', '777'] + writable_dirs)

                docker_exec(args, test_id, ['find', '/root/ansible/test/results/', '-type', 'd', '-exec', 'chmod', '777', '{}', '+'])

                docker_exec(args, test_id, ['chmod', '755', '/root'])
                docker_exec(args, test_id, ['chmod', '644', '/root/ansible/%s' % args.metadata_path])

                docker_exec(args, test_id, ['useradd', 'pytest', '--create-home'])

                docker_exec(args, test_id, cmd + ['--requirements-mode', 'only'], options=cmd_options)

                networks = get_docker_networks(args, test_id)

                for network in networks:
                    docker_network_disconnect(args, test_id, network)

                cmd += ['--requirements-mode', 'skip']

                cmd_options += ['--user', 'pytest']

            try:
                docker_exec(args, test_id, cmd, options=cmd_options)
            finally:
                with tempfile.NamedTemporaryFile(prefix='ansible-result-', suffix='.tgz') as local_result_fd:
                    docker_exec(args, test_id, ['tar', 'czf', '/root/results.tgz', '-C', '/root/ansible/test', 'results'])
                    docker_get(args, test_id, '/root/results.tgz', local_result_fd.name)
                    run_command(args, ['tar', 'oxzf', local_result_fd.name, '-C', 'test'])
        finally:
            if httptester_id:
                docker_rm(args, httptester_id)

            if test_id:
                docker_rm(args, test_id)


def delegate_remote(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    """
    parts = args.remote.split('/', 1)

    platform = parts[0]
    version = parts[1]

    core_ci = AnsibleCoreCI(args, platform, version, stage=args.remote_stage, provider=args.remote_provider)
    success = False

    if isinstance(args, ShellConfig):
        use_httptester = args.httptester
    else:
        use_httptester = args.httptester and any('needs/httptester/' in target.aliases for target in integration_targets)

    if use_httptester and not docker_available():
        display.warning('Assuming --disable-httptester since `docker` is not available.')
        use_httptester = False

    httptester_id = None
    ssh_options = []

    try:
        core_ci.start()

        if use_httptester:
            httptester_id, ssh_options = start_httptester(args)

        core_ci.wait()

        if platform == 'windows':
            # Windows doesn't need the ansible-test fluff, just run the SSH command
            manage = ManageWindowsCI(core_ci)
            cmd = ['powershell.exe']
        else:
            options = {
                '--remote': 1,
            }

            cmd = generate_command(args, 'ansible/bin/ansible-test', options, exclude, require)

            if httptester_id:
                cmd += ['--inject-httptester']

            if isinstance(args, TestConfig):
                if args.coverage and not args.coverage_label:
                    cmd += ['--coverage-label', 'remote-%s-%s' % (platform, version)]

            if isinstance(args, IntegrationConfig):
                if not args.allow_destructive:
                    cmd.append('--allow-destructive')

            # remote instances are only expected to have a single python version available
            if isinstance(args, UnitsConfig) and not args.python:
                cmd += ['--python', 'default']

            manage = ManagePosixCI(core_ci)

        manage.setup()
        if isinstance(args, IntegrationConfig):
            cloud_platforms = get_cloud_providers(args)

            for cloud_platform in cloud_platforms:
                ssh_options += cloud_platform.get_remote_ssh_options()

        try:
            manage.ssh(cmd, ssh_options)
            success = True
        finally:
            if platform != 'windows':
                manage.ssh('rm -rf /tmp/results && cp -a ansible/test/results /tmp/results && chmod -R a+r /tmp/results')
                manage.download('/tmp/results', 'test')
    finally:
        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            core_ci.stop()

        if httptester_id:
            docker_rm(args, httptester_id)


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
    options['--truncate'] = 1
    options['--redact'] = 0

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
            '--exclude': 1,
            '--require': 1,
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

    for arg in args.delegate_args:
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

    yield '--truncate'
    yield '%d' % args.truncate

    if args.redact:
        yield '--redact'
