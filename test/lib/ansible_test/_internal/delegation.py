"""Delegate test execution to another environment."""
from __future__ import annotations

import contextlib
import json
import os
import tempfile
import typing as t

from .io import (
    make_dirs,
)

from .config import (
    EnvironmentConfig,
    IntegrationConfig,
    SanityConfig,
    ShellConfig,
    TestConfig,
    UnitsConfig,
)

from .util import (
    SubprocessError,
    display,
    filter_args,
    ANSIBLE_BIN_PATH,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
)

from .util_common import (
    ResultType,
    process_scoped_temporary_directory,
)

from .containers import (
    support_container_context,
)

from .data import (
    data_context,
)

from .payload import (
    create_payload,
)

from .ci import (
    get_ci_provider,
)

from .host_configs import (
    OriginConfig,
    PythonConfig,
    VirtualPythonConfig,
)

from .connections import (
    Connection,
    DockerConnection,
    SshConnection,
    LocalConnection,
)

from .provisioning import (
    HostState,
)


@contextlib.contextmanager
def delegation_context(args, host_state):  # type: (EnvironmentConfig, HostState) -> None
    """Context manager for serialized host state during delegation."""
    make_dirs(ResultType.TMP.path)

    # noinspection PyUnusedLocal
    python = host_state.controller_profile.python  # make sure the python interpreter has been initialized before serializing host state
    del python

    with tempfile.TemporaryDirectory(prefix='host-', dir=ResultType.TMP.path) as host_dir:
        args.host_settings.serialize(os.path.join(host_dir, 'settings.dat'))
        host_state.serialize(os.path.join(host_dir, 'state.dat'))

        args.host_path = os.path.join(ResultType.TMP.relative_path, os.path.basename(host_dir))

        try:
            yield
        finally:
            args.host_path = None


def delegate(args, host_state, exclude, require):  # type: (EnvironmentConfig, HostState, t.List[str], t.List[str]) -> None
    """Delegate execution of ansible-test to another environment."""
    with delegation_context(args, host_state):
        if isinstance(args, TestConfig):
            args.metadata.ci_provider = get_ci_provider().code

            make_dirs(ResultType.TMP.path)

            with tempfile.NamedTemporaryFile(prefix='metadata-', suffix='.json', dir=ResultType.TMP.path) as metadata_fd:
                args.metadata_path = os.path.join(ResultType.TMP.relative_path, os.path.basename(metadata_fd.name))
                args.metadata.to_file(args.metadata_path)

                try:
                    delegate_command(args, host_state, exclude, require)
                finally:
                    args.metadata_path = None
        else:
            delegate_command(args, host_state, exclude, require)


def delegate_command(args, host_state, exclude, require):  # type: (EnvironmentConfig, HostState, t.List[str], t.List[str]) -> None
    """Delegate execution based on the provided host state."""
    con = host_state.controller_profile.get_origin_controller_connection()
    working_directory = host_state.controller_profile.get_working_directory()
    host_delegation = not isinstance(args.controller, OriginConfig)

    if host_delegation:
        if data_context().content.collection:
            content_root = os.path.join(working_directory, data_context().content.collection.directory)
        else:
            content_root = os.path.join(working_directory, 'ansible')

        ansible_bin_path = os.path.join(working_directory, 'ansible', 'bin')

        with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as payload_file:
            create_payload(args, payload_file.name)
            con.extract_archive(chdir=working_directory, src=payload_file)
    else:
        content_root = working_directory
        ansible_bin_path = ANSIBLE_BIN_PATH

    command = generate_command(args, host_state.controller_profile.python, ansible_bin_path, content_root, exclude, require)

    if isinstance(con, SshConnection):
        ssh = con.settings
    else:
        ssh = None

    options = []

    if isinstance(args, IntegrationConfig) and args.controller.is_managed and all(target.is_managed for target in args.targets):
        if not args.allow_destructive:
            options.append('--allow-destructive')

    with support_container_context(args, ssh) as containers:
        if containers:
            options.extend(['--containers', json.dumps(containers.to_dict())])

        # Run unit tests unprivileged to prevent stray writes to the source tree.
        # Also disconnect from the network once requirements have been installed.
        if isinstance(args, UnitsConfig) and isinstance(con, DockerConnection):
            pytest_user = 'pytest'

            writable_dirs = [
                os.path.join(content_root, ResultType.JUNIT.relative_path),
                os.path.join(content_root, ResultType.COVERAGE.relative_path),
            ]

            con.run(['mkdir', '-p'] + writable_dirs)
            con.run(['chmod', '777'] + writable_dirs)
            con.run(['chmod', '755', working_directory])
            con.run(['chmod', '644', os.path.join(content_root, args.metadata_path)])
            con.run(['useradd', pytest_user, '--create-home'])
            con.run(insert_options(command, options + ['--requirements-mode', 'only']))

            container = con.inspect()
            networks = container.get_network_names()

            if networks is not None:
                for network in networks:
                    con.disconnect_network(network)
            else:
                display.warning('Network disconnection is not supported (this is normal under podman). '
                                'Tests will not be isolated from the network. Network-related tests may misbehave.')

            options.extend(['--requirements-mode', 'skip'])

            con.user = pytest_user

        success = False

        try:
            con.run(insert_options(command, options))
            success = True
        finally:
            if host_delegation:
                download_results(args, con, content_root, success)


def insert_options(command, options):
    """Insert addition command line options into the given command and return the result."""
    result = []

    for arg in command:
        if options and arg.startswith('--'):
            result.extend(options)
            options = None

        result.append(arg)

    return result


def download_results(args, con, content_root, success):  # type: (EnvironmentConfig, Connection, str, bool) -> None
    """Download results from a delegated controller."""
    remote_results_root = os.path.join(content_root, data_context().content.results_path)
    local_test_root = os.path.dirname(os.path.join(data_context().content.root, data_context().content.results_path))

    remote_test_root = os.path.dirname(remote_results_root)
    remote_results_name = os.path.basename(remote_results_root)

    make_dirs(local_test_root)  # make sure directory exists for collections which have no tests

    with tempfile.NamedTemporaryFile(prefix='ansible-test-result-', suffix='.tgz') as result_file:
        try:
            con.create_archive(chdir=remote_test_root, name=remote_results_name, dst=result_file, exclude=ResultType.TMP.name)
        except SubprocessError as ex:
            if success:
                raise  # download errors are fatal if tests succeeded

            # surface download failures as a warning here to avoid masking test failures
            display.warning(f'Failed to download results while handling an exception: {ex}')
        else:
            result_file.seek(0)

            local_con = LocalConnection(args)
            local_con.extract_archive(chdir=local_test_root, src=result_file)


def generate_command(
        args,  # type: EnvironmentConfig
        python,  # type: PythonConfig
        ansible_bin_path,  # type: str
        content_root,  # type: str
        exclude,  # type: t.List[str]
        require,  # type: t.List[str]
):  # type: (...) -> t.List[str]
    """Generate the command necessary to delegate ansible-test."""
    options = {
        '--color': 1,
        '--docker-no-pull': 0,
    }

    cmd = [os.path.join(ansible_bin_path, 'ansible-test')]
    cmd = [python.path] + cmd

    # Force the encoding used during delegation.
    # This is only needed because ansible-test relies on Python's file system encoding.
    # Environments that do not have the locale configured are thus unable to work with unicode file paths.
    # Examples include FreeBSD and some Linux containers.
    env_vars = dict(
        LC_ALL='en_US.UTF-8',
        ANSIBLE_TEST_CONTENT_ROOT=content_root,
    )

    if isinstance(args.controller.python, VirtualPythonConfig):
        # Expose the ansible and ansible_test library directories to the virtual environment.
        # This is only required when running from an install.
        library_path = process_scoped_temporary_directory(args)

        os.symlink(ANSIBLE_LIB_ROOT, os.path.join(library_path, 'ansible'))
        os.symlink(ANSIBLE_TEST_ROOT, os.path.join(library_path, 'ansible_test'))

        env_vars.update(
            PYTHONPATH=library_path,
        )

    # Propagate the TERM environment variable to the remote host when using the shell command.
    if isinstance(args, ShellConfig):
        term = os.environ.get('TERM')

        if term is not None:
            env_vars.update(TERM=term)

    env_args = ['%s=%s' % (key, env_vars[key]) for key in sorted(env_vars)]

    cmd = ['/usr/bin/env'] + env_args + cmd

    cmd += list(filter_options(args, args.host_settings.filtered_args, options, exclude, require))
    cmd += ['--color', 'yes' if args.color else 'no']

    if isinstance(args, SanityConfig):
        base_branch = args.base_branch or get_ci_provider().get_base_branch()

        if base_branch:
            cmd += ['--base-branch', base_branch]

    cmd.extend(['--host-path', args.host_path])

    return cmd


def filter_options(
        args,  # type: EnvironmentConfig
        argv,  # type: t.List[str]
        options,  # type: t.Dict[str, int]
        exclude,  # type: t.List[str]
        require,  # type: t.List[str]
):  # type: (...) -> t.Iterable[str]
    """Return an iterable that filters out unwanted CLI options and injects new ones as requested."""
    options = options.copy()

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

    if isinstance(args, IntegrationConfig):
        options.update({
            '--no-temp-unicode': 0,
        })

    for arg in filter_args(argv, options):
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

    if not args.redact:
        yield '--no-redact'

    if isinstance(args, IntegrationConfig):
        if args.no_temp_unicode:
            yield '--no-temp-unicode'
