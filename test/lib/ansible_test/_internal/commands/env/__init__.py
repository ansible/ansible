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
    get_ansible_version,
    get_available_python_versions,
    ApplicationError,
)

from ...util_common import (
    data_context,
    write_json_test_results,
    ResultType,
)

from ...docker_util import (
    get_docker_command,
    get_docker_info,
    get_docker_container_id,
)

from ...constants import (
    TIMEOUT_PATH,
)

from ...ci import (
    get_ci_provider,
)

from ...timeout import (
    TimeoutDetail,
)


class EnvConfig(CommonConfig):
    """Configuration for the `env` command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'env')

        self.show: bool = args.show
        self.dump: bool = args.dump
        self.timeout: int | float | None = args.timeout
        self.list_files: bool = args.list_files

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

    container_id = get_docker_container_id()

    data = dict(
        ansible=dict(
            version=get_ansible_version(),
        ),
        docker=get_docker_details(args),
        container_id=container_id,
        environ=os.environ.copy(),
        location=dict(
            pwd=os.environ.get('PWD', None),
            cwd=os.getcwd(),
        ),
        git=get_ci_provider().get_git_details(args),
        platform=dict(
            datetime=datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
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

    timeout = TimeoutDetail.create(args.timeout)

    if timeout:
        display.info(f'Setting a {timeout.duration} minute test timeout which will end at: {timeout.deadline}', verbosity=1)
    else:
        display.info('Clearing existing test timeout.', verbosity=1)

    if args.explain:
        return

    if timeout:
        write_json_file(TIMEOUT_PATH, timeout.to_dict())
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
            docker_info = get_docker_info(args)
        except ApplicationError as ex:
            display.warning(str(ex))
        else:
            info = docker_info.info
            version = docker_info.version

    docker_details = dict(
        executable=executable,
        info=info,
        version=version,
    )

    return docker_details
