"""Show information about the test environment."""
from __future__ import annotations

import datetime
import os
import platform
import sys
import typing as t

from ...config import (
    CommonConfig,
)

from ...io import (
    write_json_file,
)

from ...util import (
    display,
    SubprocessError,
    get_ansible_version,
    get_available_python_versions,
)

from ...util_common import (
    data_context,
    write_json_test_results,
    ResultType,
)

from ...docker_util import (
    get_docker_command,
    docker_info,
    docker_version
)

from ...constants import (
    TIMEOUT_PATH,
)

from ...ci import (
    get_ci_provider,
)


class EnvConfig(CommonConfig):
    """Configuration for the `env` command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'env')

        self.show = args.show
        self.dump = args.dump
        self.timeout = args.timeout
        self.list_files = args.list_files

        if not self.show and not self.dump and self.timeout is None and not self.list_files:
            # default to --show if no options were given
            self.show = True


def command_env(args: EnvConfig) -> None:
    """Entry point for the `env` command."""
    show_dump_env(args)
    list_files_env(args)
    set_timeout(args)


def show_dump_env(args: EnvConfig) -> None:
    """Show information about the current environment and/or write the information to disk."""
    if not args.show and not args.dump:
        return

    data = dict(
        ansible=dict(
            version=get_ansible_version(),
        ),
        docker=get_docker_details(args),
        environ=os.environ.copy(),
        location=dict(
            pwd=os.environ.get('PWD', None),
            cwd=os.getcwd(),
        ),
        git=get_ci_provider().get_git_details(args),
        platform=dict(
            datetime=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            platform=platform.platform(),
            uname=platform.uname(),
        ),
        python=dict(
            executable=sys.executable,
            version=platform.python_version(),
        ),
        interpreters=get_available_python_versions(),
    )

    if args.show:
        verbose = {
            'docker': 3,
            'docker.executable': 0,
            'environ': 2,
            'platform.uname': 1,
        }

        show_dict(data, verbose)

    if args.dump and not args.explain:
        write_json_test_results(ResultType.BOT, 'data-environment.json', data)


def list_files_env(args: EnvConfig) -> None:
    """List files on stdout."""
    if not args.list_files:
        return

    for path in data_context().content.all_files():
        display.info(path)


def set_timeout(args: EnvConfig) -> None:
    """Set an execution timeout for subsequent ansible-test invocations."""
    if args.timeout is None:
        return

    if args.timeout:
        deadline = (datetime.datetime.utcnow() + datetime.timedelta(minutes=args.timeout)).strftime('%Y-%m-%dT%H:%M:%SZ')

        display.info('Setting a %d minute test timeout which will end at: %s' % (args.timeout, deadline), verbosity=1)
    else:
        deadline = None

        display.info('Clearing existing test timeout.', verbosity=1)

    if args.explain:
        return

    if deadline:
        data = dict(
            duration=args.timeout,
            deadline=deadline,
        )

        write_json_file(TIMEOUT_PATH, data)
    elif os.path.exists(TIMEOUT_PATH):
        os.remove(TIMEOUT_PATH)


def show_dict(data: dict[str, t.Any], verbose: dict[str, int], root_verbosity: int = 0, path: t.Optional[list[str]] = None) -> None:
    """Show a dict with varying levels of verbosity."""
    path = path if path else []

    for key, value in sorted(data.items()):
        indent = '  ' * len(path)
        key_path = path + [key]
        key_name = '.'.join(key_path)
        verbosity = verbose.get(key_name, root_verbosity)

        if isinstance(value, (tuple, list)):
            display.info(indent + '%s:' % key, verbosity=verbosity)
            for item in value:
                display.info(indent + '  - %s' % item, verbosity=verbosity)
        elif isinstance(value, dict):
            min_verbosity = min([verbosity] + [v for k, v in verbose.items() if k.startswith('%s.' % key)])
            display.info(indent + '%s:' % key, verbosity=min_verbosity)
            show_dict(value, verbose, verbosity, key_path)
        else:
            display.info(indent + '%s: %s' % (key, value), verbosity=verbosity)


def get_docker_details(args: EnvConfig) -> dict[str, t.Any]:
    """Return details about docker."""
    docker = get_docker_command()

    executable = None
    info = None
    version = None

    if docker:
        executable = docker.executable

        try:
            info = docker_info(args)
        except SubprocessError as ex:
            display.warning('Failed to collect docker info:\n%s' % ex)

        try:
            version = docker_version(args)
        except SubprocessError as ex:
            display.warning('Failed to collect docker version:\n%s' % ex)

    docker_details = dict(
        executable=executable,
        info=info,
        version=version,
    )

    return docker_details
