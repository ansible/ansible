"""Delegate test execution to another environment."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import sys
import tempfile

from . import types as t

from .executor import (
    SUPPORTED_PYTHON_VERSIONS,
    HTTPTESTER_HOSTS,
    create_shell_command,
    run_httptester,
    start_httptester,
    get_python_interpreter,
    get_python_version,
    get_docker_completion,
    get_remote_completion,
)

from .config import (
    TestConfig,
    EnvironmentConfig,
    IntegrationConfig,
    WindowsIntegrationConfig,
    NetworkIntegrationConfig,
    ShellConfig,
    SanityConfig,
    UnitsConfig,
)

from .core_ci import (
    AnsibleCoreCI,
)

from .manage_ci import (
    ManagePosixCI,
    ManageWindowsCI,
)

from .util import (
    ApplicationError,
    common_environment,
    pass_vars,
    display,
    ANSIBLE_BIN_PATH,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
    tempdir,
    make_dirs,
)

from .util_common import (
    run_command,
    ResultType,
    create_interpreter_wrapper,
)

from .docker_util import (
    docker_exec,
    docker_get,
    docker_pull,
    docker_put,
    docker_rm,
    docker_run,
    docker_available,
    docker_network_disconnect,
    get_docker_networks,
    get_docker_preferred_network_name,
    get_docker_hostname,
    is_docker_user_defined_network,
)

from .cloud import (
    get_cloud_providers,
)

from .target import (
    IntegrationTarget,
)

from .data import (
    data_context,
)

from .payload import (
    create_payload,
)

from .venv import (
    create_virtual_environment,
)

from .ci import (
    get_ci_provider,
)


def check_delegation_args(args):
    """
    :type args: CommonConfig
    """
    if not isinstance(args, EnvironmentConfig):
        return

    if args.docker:
        get_python_version(args, get_docker_completion(), args.docker_raw)
    elif args.remote:
        get_python_version(args, get_remote_completion(), args.remote)


def delegate(args, exclude, require, integration_targets):
    """
    :type args: EnvironmentConfig
    :type exclude: list[str]
    :type require: list[str]
    :type integration_targets: tuple[IntegrationTarget]
    :rtype: bool
    """
    if isinstance(args, TestConfig):
        args.metadata.ci_provider = get_ci_provider().code

        with tempfile.NamedTemporaryFile(prefix='metadata-', suffix='.json', dir=data_context().content.root) as metadata_fd:
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
    if args.venv:
        delegate_venv(args, exclude, require, integration_targets)
        return True

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
        versions = (args.python_version,)

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
        tox = ['tox', '-c', os.path.join(ANSIBLE_TEST_DATA_ROOT, 'tox.ini'), '-e', 'py' + version.replace('.', '')]

        if args.tox_sitepackages:
            tox.append('--sitepackages')

        tox.append('--')

        cmd = generate_command(args, None, ANSIBLE_BIN_PATH, data_context().content.root, options, exclude, require)

        if not args.python:
            cmd += ['--python', version]

        # newer versions of tox do not support older python versions and will silently fall back to a different version
        # passing this option will allow the delegated ansible-test to verify it is running under the expected python version
        # tox 3.0.0 dropped official python 2.6 support: https://tox.readthedocs.io/en/latest/changelog.html#v3-0-0-2018-04-02
        # tox 3.1.3 is the first version to support python 3.8 and later: https://tox.readthedocs.io/en/latest/changelog.html#v3-1-3-2018-08-03
        # tox 3.1.3 appears to still work with python 2.6, making it a good version to use when supporting all python versions we use
        # virtualenv 16.0.0 dropped python 2.6 support: https://virtualenv.pypa.io/en/latest/changes/#v16-0-0-2018-05-16
        cmd += ['--check-python', version]

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


def delegate_venv(args,  # type: EnvironmentConfig
                  exclude,  # type: t.List[str]
                  require,  # type: t.List[str]
                  integration_targets,  # type: t.Tuple[IntegrationTarget, ...]
                  ):  # type: (...) -> None
    """Delegate ansible-test execution to a virtual environment using venv or virtualenv."""
    if args.python:
        versions = (args.python_version,)
    else:
        versions = SUPPORTED_PYTHON_VERSIONS

    if args.httptester:
        needs_httptester = sorted(target.name for target in integration_targets if 'needs/httptester/' in target.aliases)

        if needs_httptester:
            display.warning('Use --docker or --remote to enable httptester for tests marked "needs/httptester": %s' % ', '.join(needs_httptester))

    if args.venv_system_site_packages:
        suffix = '-ssp'
    else:
        suffix = ''

    venvs = dict((version, os.path.join(ResultType.TMP.path, 'delegation', 'python%s%s' % (version, suffix))) for version in versions)
    venvs = dict((version, path) for version, path in venvs.items() if create_virtual_environment(args, version, path, args.venv_system_site_packages))

    if not venvs:
        raise ApplicationError('No usable virtual environment support found.')

    options = {
        '--venv': 0,
        '--venv-system-site-packages': 0,
    }

    with tempdir() as inject_path:
        for version, path in venvs.items():
            create_interpreter_wrapper(os.path.join(path, 'bin', 'python'), os.path.join(inject_path, 'python%s' % version))

        python_interpreter = os.path.join(inject_path, 'python%s' % args.python_version)

        cmd = generate_command(args, python_interpreter, ANSIBLE_BIN_PATH, data_context().content.root, options, exclude, require)

        if isinstance(args, TestConfig):
            if args.coverage and not args.coverage_label:
                cmd += ['--coverage-label', 'venv']

        env = common_environment()

        with tempdir() as library_path:
            # expose ansible and ansible_test to the virtual environment (only required when running from an install)
            os.symlink(ANSIBLE_LIB_ROOT, os.path.join(library_path, 'ansible'))
            os.symlink(ANSIBLE_TEST_ROOT, os.path.join(library_path, 'ansible_test'))

            env.update(
                PATH=inject_path + os.pathsep + env['PATH'],
                PYTHONPATH=library_path,
            )

            run_command(args, cmd, env=env)


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

    python_interpreter = get_python_interpreter(args, get_docker_completion(), args.docker_raw)

    install_root = '/root/ansible'

    if data_context().content.collection:
        content_root = os.path.join(install_root, data_context().content.collection.directory)
    else:
        content_root = install_root

    remote_results_root = os.path.join(content_root, data_context().content.results_path)

    cmd = generate_command(args, python_interpreter, os.path.join(install_root, 'bin'), content_root, options, exclude, require)

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
            create_payload(args, local_source_fd.name)

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

            if get_docker_hostname() != 'localhost' or os.path.exists(docker_socket):
                test_options += ['--volume', '%s:%s' % (docker_socket, docker_socket)]

            if httptester_id:
                test_options += ['--env', 'HTTPTESTER=1']

                network = get_docker_preferred_network_name(args)

                if not is_docker_user_defined_network(network):
                    # legacy links are required when using the default bridge network instead of user-defined networks
                    for host in HTTPTESTER_HOSTS:
                        test_options += ['--link', '%s:%s' % (httptester_id, host)]

            if isinstance(args, IntegrationConfig):
                cloud_platforms = get_cloud_providers(args)

                for cloud_platform in cloud_platforms:
                    test_options += cloud_platform.get_docker_run_options()

            test_id = docker_run(args, test_image, options=test_options)[0]

            if args.explain:
                test_id = 'test_id'
            else:
                test_id = test_id.strip()

            # write temporary files to /root since /tmp isn't ready immediately on container start
            docker_put(args, test_id, os.path.join(ANSIBLE_TEST_DATA_ROOT, 'setup', 'docker.sh'), '/root/docker.sh')
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
                    os.path.join(content_root, ResultType.JUNIT.relative_path),
                    os.path.join(content_root, ResultType.COVERAGE.relative_path),
                ]

                docker_exec(args, test_id, ['mkdir', '-p'] + writable_dirs)
                docker_exec(args, test_id, ['chmod', '777'] + writable_dirs)
                docker_exec(args, test_id, ['chmod', '755', '/root'])
                docker_exec(args, test_id, ['chmod', '644', os.path.join(content_root, args.metadata_path)])

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
                local_test_root = os.path.dirname(os.path.join(data_context().content.root, data_context().content.results_path))

                remote_test_root = os.path.dirname(remote_results_root)
                remote_results_name = os.path.basename(remote_results_root)
                remote_temp_file = os.path.join('/root', remote_results_name + '.tgz')

                with tempfile.NamedTemporaryFile(prefix='ansible-result-', suffix='.tgz') as local_result_fd:
                    docker_exec(args, test_id, ['tar', 'czf', remote_temp_file, '--exclude', ResultType.TMP.name, '-C', remote_test_root, remote_results_name])
                    docker_get(args, test_id, remote_temp_file, local_result_fd.name)
                    run_command(args, ['tar', 'oxzf', local_result_fd.name, '-C', local_test_root])
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
    raw = False

    if isinstance(args, ShellConfig):
        use_httptester = args.httptester
        raw = args.raw
    else:
        use_httptester = args.httptester and any('needs/httptester/' in target.aliases for target in integration_targets)

    if use_httptester and not docker_available():
        display.warning('Assuming --disable-httptester since `docker` is not available.')
        use_httptester = False

    httptester_id = None
    ssh_options = []
    content_root = None

    try:
        core_ci.start()

        if use_httptester:
            httptester_id, ssh_options = start_httptester(args)

        core_ci.wait()

        python_version = get_python_version(args, get_remote_completion(), args.remote)

        if platform == 'windows':
            # Windows doesn't need the ansible-test fluff, just run the SSH command
            manage = ManageWindowsCI(core_ci)
            manage.setup(python_version)

            cmd = ['powershell.exe']
        elif raw:
            manage = ManagePosixCI(core_ci)
            manage.setup(python_version)

            cmd = create_shell_command(['bash'])
        else:
            manage = ManagePosixCI(core_ci)
            pwd = manage.setup(python_version)

            options = {
                '--remote': 1,
            }

            python_interpreter = get_python_interpreter(args, get_remote_completion(), args.remote)

            install_root = os.path.join(pwd, 'ansible')

            if data_context().content.collection:
                content_root = os.path.join(install_root, data_context().content.collection.directory)
            else:
                content_root = install_root

            cmd = generate_command(args, python_interpreter, os.path.join(install_root, 'bin'), content_root, options, exclude, require)

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

        if isinstance(args, IntegrationConfig):
            cloud_platforms = get_cloud_providers(args)

            for cloud_platform in cloud_platforms:
                ssh_options += cloud_platform.get_remote_ssh_options()

        try:
            manage.ssh(cmd, ssh_options)
            success = True
        finally:
            download = False

            if platform != 'windows':
                download = True

            if isinstance(args, ShellConfig):
                if args.raw:
                    download = False

            if download and content_root:
                local_test_root = os.path.dirname(os.path.join(data_context().content.root, data_context().content.results_path))

                remote_results_root = os.path.join(content_root, data_context().content.results_path)
                remote_results_name = os.path.basename(remote_results_root)
                remote_temp_path = os.path.join('/tmp', remote_results_name)

                manage.ssh('rm -rf {0} && mkdir {0} && cp -a {1}/* {0}/ && chmod -R a+r {0}'.format(remote_temp_path, remote_results_root))
                manage.download(remote_temp_path, local_test_root)
    finally:
        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            core_ci.stop()

        if httptester_id:
            docker_rm(args, httptester_id)


def generate_command(args, python_interpreter, ansible_bin_path, content_root, options, exclude, require):
    """
    :type args: EnvironmentConfig
    :type python_interpreter: str | None
    :type ansible_bin_path: str
    :type content_root: str
    :type options: dict[str, int]
    :type exclude: list[str]
    :type require: list[str]
    :rtype: list[str]
    """
    options['--color'] = 1

    cmd = [os.path.join(ansible_bin_path, 'ansible-test')]

    if python_interpreter:
        cmd = [python_interpreter] + cmd

    # Force the encoding used during delegation.
    # This is only needed because ansible-test relies on Python's file system encoding.
    # Environments that do not have the locale configured are thus unable to work with unicode file paths.
    # Examples include FreeBSD and some Linux containers.
    env_vars = dict(
        LC_ALL='en_US.UTF-8',
        ANSIBLE_TEST_CONTENT_ROOT=content_root,
    )

    env_args = ['%s=%s' % (key, env_vars[key]) for key in sorted(env_vars)]

    cmd = ['/usr/bin/env'] + env_args + cmd

    cmd += list(filter_options(args, sys.argv[1:], options, exclude, require))
    cmd += ['--color', 'yes' if args.color else 'no']

    if args.requirements:
        cmd += ['--requirements']

    if isinstance(args, ShellConfig):
        cmd = create_shell_command(cmd)
    elif isinstance(args, SanityConfig):
        base_branch = args.base_branch or get_ci_provider().get_base_branch()

        if base_branch:
            cmd += ['--base-branch', base_branch]

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
    options['--no-redact'] = 0

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

    if isinstance(args, (NetworkIntegrationConfig, WindowsIntegrationConfig)):
        options.update({
            '--inventory': 1,
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
    else:
        yield '--no-redact'
