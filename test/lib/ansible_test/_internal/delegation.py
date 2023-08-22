"""Delegate test execution to another environment."""
from __future__ import annotations

import collections.abc as c
import contextlib
import json
import os
import tempfile
import typing as t

from .constants import (
    STATUS_HOST_CONNECTION_ERROR,
)

from .locale_util import (
    STANDARD_LOCALE,
)

from .io import (
    make_dirs,
)

from .config import (
    CommonConfig,
    EnvironmentConfig,
    IntegrationConfig,
    ShellConfig,
    TestConfig,
    UnitsConfig,
)

from .util import (
    SubprocessError,
    display,
    filter_args,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
    OutputStream,
)

from .util_common import (
    ResultType,
    process_scoped_temporary_directory,
)

from .ansible_util import (
    get_ansible_bin_path,
)

from .containers import (
    support_container_context,
    ContainerDatabase,
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

from .content_config import (
    serialize_content_config,
)


@contextlib.contextmanager
def delegation_context(args: EnvironmentConfig, host_state: HostState) -> c.Iterator[None]:
    """Context manager for serialized host state during delegation."""
    make_dirs(ResultType.TMP.path)

    # noinspection PyUnusedLocal
    python = host_state.controller_profile.python  # make sure the python interpreter has been initialized before serializing host state
    del python

    with tempfile.TemporaryDirectory(prefix='host-', dir=ResultType.TMP.path) as host_dir:
        args.host_settings.serialize(os.path.join(host_dir, 'settings.dat'))
        host_state.serialize(os.path.join(host_dir, 'state.dat'))
        serialize_content_config(args, os.path.join(host_dir, 'config.dat'))

        args.host_path = os.path.join(ResultType.TMP.relative_path, os.path.basename(host_dir))

        try:
            yield
        finally:
            args.host_path = None


def delegate(args: CommonConfig, host_state: HostState, exclude: list[str], require: list[str]) -> None:
    """Delegate execution of ansible-test to another environment."""
    assert isinstance(args, EnvironmentConfig)

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


def delegate_command(args: EnvironmentConfig, host_state: HostState, exclude: list[str], require: list[str]) -> None:
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
        ansible_bin_path = get_ansible_bin_path(args)

    command = generate_command(args, host_state.controller_profile.python, ansible_bin_path, content_root, exclude, require)

    if isinstance(con, SshConnection):
        ssh = con.settings
    else:
        ssh = None

    options = []

    if isinstance(args, IntegrationConfig) and args.controller.is_managed and all(target.is_managed for target in args.targets):
        if not args.allow_destructive:
            options.append('--allow-destructive')

    with support_container_context(args, ssh) as containers:  # type: t.Optional[ContainerDatabase]
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

            con.run(['mkdir', '-p'] + writable_dirs, capture=True)
            con.run(['chmod', '777'] + writable_dirs, capture=True)
            con.run(['chmod', '755', working_directory], capture=True)
            con.run(['useradd', pytest_user, '--create-home'], capture=True)

            con.run(insert_options(command, options + ['--requirements-mode', 'only']), capture=False)

            container = con.inspect()
            networks = container.get_network_names()

            if networks is not None:
                for network in networks:
                    try:
                        con.disconnect_network(network)
                    except SubprocessError:
                        display.warning(
                            'Unable to disconnect network "%s" (this is normal under podman). '
                            'Tests will not be isolated from the network. Network-related tests may '
                            'misbehave.' % (network,)
                        )
            else:
                display.warning('Network disconnection is not supported (this is normal under podman). '
                                'Tests will not be isolated from the network. Network-related tests may misbehave.')

            options.extend(['--requirements-mode', 'skip'])

            con.user = pytest_user

        success = False
        status = 0

        try:
            # When delegating, preserve the original separate stdout/stderr streams, but only when the following conditions are met:
            # 1) Display output is being sent to stderr. This indicates the output on stdout must be kept separate from stderr.
            # 2) The delegation is non-interactive. Interactive mode, which generally uses a TTY, is not compatible with intercepting stdout/stderr.
            # The downside to having separate streams is that individual lines of output from each are more likely to appear out-of-order.
            output_stream = OutputStream.ORIGINAL if args.display_stderr and not args.interactive else None
            con.run(insert_options(command, options), capture=False, interactive=args.interactive, output_stream=output_stream)
            success = True
        except SubprocessError as ex:
            status = ex.status
            raise
        finally:
            if host_delegation:
                download_results(args, con, content_root, success)

            if not success and status == STATUS_HOST_CONNECTION_ERROR:
                for target in host_state.target_profiles:
                    target.on_target_failure()  # when the controller is delegated, report failures after delegation fails


def insert_options(command: list[str], options: list[str]) -> list[str]:
    """Insert addition command line options into the given command and return the result."""
    result = []

    for arg in command:
        if options and arg.startswith('--'):
            result.extend(options)
            options = None

        result.append(arg)

    return result


def download_results(args: EnvironmentConfig, con: Connection, content_root: str, success: bool) -> None:
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
    args: EnvironmentConfig,
    python: PythonConfig,
    ansible_bin_path: str,
    content_root: str,
    exclude: list[str],
    require: list[str],
) -> list[str]:
    """Generate the command necessary to delegate ansible-test."""
    cmd = [os.path.join(ansible_bin_path, 'ansible-test')]
    cmd = [python.path] + cmd

    env_vars = dict(
        ANSIBLE_TEST_CONTENT_ROOT=content_root,
    )

    if isinstance(args.controller, OriginConfig):
        # Expose the ansible and ansible_test library directories to the Python environment.
        # This is only required when delegation is used on the origin host.
        library_path = process_scoped_temporary_directory(args)

        os.symlink(ANSIBLE_LIB_ROOT, os.path.join(library_path, 'ansible'))
        os.symlink(ANSIBLE_TEST_ROOT, os.path.join(library_path, 'ansible_test'))

        env_vars.update(
            PYTHONPATH=library_path,
        )
    else:
        # When delegating to a host other than the origin, the locale must be explicitly set.
        # Setting of the locale for the origin host is handled by common_environment().
        # Not all connections support setting the locale, and for those that do, it isn't guaranteed to work.
        # This is needed to make sure the delegated environment is configured for UTF-8 before running Python.
        env_vars.update(
            LC_ALL=STANDARD_LOCALE,
        )

    # Propagate the TERM environment variable to the remote host when using the shell command.
    if isinstance(args, ShellConfig):
        term = os.environ.get('TERM')

        if term is not None:
            env_vars.update(TERM=term)

    env_args = ['%s=%s' % (key, env_vars[key]) for key in sorted(env_vars)]

    cmd = ['/usr/bin/env'] + env_args + cmd

    cmd += list(filter_options(args, args.host_settings.filtered_args, exclude, require))

    return cmd


def filter_options(
    args: EnvironmentConfig,
    argv: list[str],
    exclude: list[str],
    require: list[str],
) -> c.Iterable[str]:
    """Return an iterable that filters out unwanted CLI options and injects new ones as requested."""
    replace: list[tuple[str, int, t.Optional[t.Union[bool, str, list[str]]]]] = [
        ('--docker-no-pull', 0, False),
        ('--truncate', 1, str(args.truncate)),
        ('--color', 1, 'yes' if args.color else 'no'),
        ('--redact', 0, False),
        ('--no-redact', 0, not args.redact),
        ('--host-path', 1, args.host_path),
    ]

    if isinstance(args, TestConfig):
        replace.extend([
            ('--changed', 0, False),
            ('--tracked', 0, False),
            ('--untracked', 0, False),
            ('--ignore-committed', 0, False),
            ('--ignore-staged', 0, False),
            ('--ignore-unstaged', 0, False),
            ('--changed-from', 1, False),
            ('--changed-path', 1, False),
            ('--metadata', 1, args.metadata_path),
            ('--exclude', 1, exclude),
            ('--require', 1, require),
            ('--base-branch', 1, False),
        ])

    pass_through_args: list[str] = []

    for arg in filter_args(argv, {option: count for option, count, replacement in replace}):
        if arg == '--' or pass_through_args:
            pass_through_args.append(arg)
            continue

        yield arg

    for option, _count, replacement in replace:
        if not replacement:
            continue

        if isinstance(replacement, bool):
            yield option
        elif isinstance(replacement, str):
            yield from [option, replacement]
        elif isinstance(replacement, list):
            for item in replacement:
                yield from [option, item]

    yield from args.delegate_args
    yield from pass_through_args
