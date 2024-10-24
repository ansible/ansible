"""Miscellaneous utility functions and classes specific to ansible cli tools."""
from __future__ import annotations

import json
import os
import shutil
import typing as t

from .constants import (
    ANSIBLE_BIN_SYMLINK_MAP,
    SOFT_RLIMIT_NOFILE,
)

from .util import (
    common_environment,
    ApplicationError,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_ROOT,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_ROOT,
    ANSIBLE_SOURCE_ROOT,
    ANSIBLE_TEST_TOOLS_ROOT,
    MODE_FILE_EXECUTE,
    raw_command,
    verified_chmod,
)

from .util_common import (
    create_temp_dir,
    ResultType,
    intercept_python,
    get_injector_path,
)

from .config import (
    IntegrationConfig,
    PosixIntegrationConfig,
    EnvironmentConfig,
    CommonConfig,
)

from .data import (
    data_context,
)

from .python_requirements import (
    install_requirements,
)

from .host_configs import (
    PythonConfig,
)

from .thread import (
    mutex,
)


def parse_inventory(args: EnvironmentConfig, inventory_path: str) -> dict[str, t.Any]:
    """Return a dict parsed from the given inventory file."""
    cmd = ['ansible-inventory', '-i', inventory_path, '--list']
    env = ansible_environment(args)
    inventory = json.loads(intercept_python(args, args.controller_python, cmd, env, capture=True, always=True)[0])
    return inventory


def get_hosts(inventory: dict[str, t.Any], group_name: str) -> dict[str, dict[str, t.Any]]:
    """Return a dict of hosts from the specified group in the given inventory."""
    hostvars = inventory.get('_meta', {}).get('hostvars', {})
    group = inventory.get(group_name, {})
    host_names = group.get('hosts', [])
    hosts = dict((name, hostvars.get(name, {})) for name in host_names)
    return hosts


def ansible_environment(args: CommonConfig, color: bool = True, ansible_config: t.Optional[str] = None) -> dict[str, str]:
    """Return a dictionary of environment variables to use when running Ansible commands."""
    env = common_environment()
    path = env['PATH']

    ansible_bin_path = get_ansible_bin_path(args)

    if not path.startswith(ansible_bin_path + os.path.pathsep):
        path = ansible_bin_path + os.path.pathsep + path

    if not ansible_config:
        # use the default empty configuration unless one has been provided
        ansible_config = args.get_ansible_config()

    if not args.explain and not os.path.exists(ansible_config):
        raise ApplicationError('Configuration not found: %s' % ansible_config)

    ansible = dict(
        ANSIBLE_PYTHON_MODULE_RLIMIT_NOFILE=str(SOFT_RLIMIT_NOFILE),
        ANSIBLE_FORCE_COLOR='%s' % 'true' if args.color and color else 'false',
        ANSIBLE_FORCE_HANDLERS='true',  # allow cleanup handlers to run when tests fail
        ANSIBLE_HOST_PATTERN_MISMATCH='error',  # prevent tests from unintentionally passing when hosts are not found
        ANSIBLE_INVENTORY='/dev/null',  # force tests to provide inventory
        ANSIBLE_DEPRECATION_WARNINGS='false',
        ANSIBLE_HOST_KEY_CHECKING='false',
        ANSIBLE_RETRY_FILES_ENABLED='false',
        ANSIBLE_CONFIG=ansible_config,
        ANSIBLE_LIBRARY='/dev/null',
        ANSIBLE_DEVEL_WARNING='false',  # Don't show warnings that CI is running devel
        PYTHONPATH=get_ansible_python_path(args),
        PAGER='/bin/cat',
        PATH=path,
        # give TQM worker processes time to report code coverage results
        # without this the last task in a play may write no coverage file, an empty file, or an incomplete file
        # enabled even when not using code coverage to surface warnings when worker processes do not exit cleanly
        ANSIBLE_WORKER_SHUTDOWN_POLL_COUNT='100',
        ANSIBLE_WORKER_SHUTDOWN_POLL_DELAY='0.1',
        # ansible-test specific environment variables require an 'ANSIBLE_TEST_' prefix to distinguish them from ansible-core env vars defined by config
        ANSIBLE_TEST_ANSIBLE_LIB_ROOT=ANSIBLE_LIB_ROOT,  # used by the coverage injector
    )
    if color_term := os.getenv('COLORTERM'):
        ansible['COLORTERM'] = color_term

    if isinstance(args, IntegrationConfig) and args.coverage:
        # standard path injection is not effective for the persistent connection helper, instead the location must be configured
        # it only requires the injector for code coverage
        # the correct python interpreter is already selected using the sys.executable used to invoke ansible
        ansible.update(
            _ANSIBLE_CONNECTION_PATH=os.path.join(get_injector_path(), 'ansible_connection_cli_stub.py'),
        )

    if isinstance(args, PosixIntegrationConfig):
        ansible.update(
            ANSIBLE_PYTHON_INTERPRETER='/set/ansible_python_interpreter/in/inventory',  # force tests to set ansible_python_interpreter in inventory
        )

    env.update(ansible)

    if args.debug:
        env.update(
            ANSIBLE_DEBUG='true',
            ANSIBLE_LOG_PATH=os.path.join(ResultType.LOGS.name, 'debug.log'),
        )

    if data_context().content.collection:
        env.update(
            ANSIBLE_COLLECTIONS_PATH=data_context().content.collection.root,
        )

    if data_context().content.is_ansible:
        env.update(configure_plugin_paths(args))

    return env


def configure_plugin_paths(args: CommonConfig) -> dict[str, str]:
    """Return environment variables with paths to plugins relevant for the current command."""
    if not isinstance(args, IntegrationConfig):
        return {}

    support_path = os.path.join(ANSIBLE_SOURCE_ROOT, 'test', 'support', args.command)

    # provide private copies of collections for integration tests
    collection_root = os.path.join(support_path, 'collections')

    env = dict(
        ANSIBLE_COLLECTIONS_PATH=collection_root,
    )

    # provide private copies of plugins for integration tests
    plugin_root = os.path.join(support_path, 'plugins')

    plugin_list = [
        'action',
        'become',
        'cache',
        'callback',
        'cliconf',
        'connection',
        'filter',
        'httpapi',
        'inventory',
        'lookup',
        'netconf',
        # 'shell' is not configurable
        'strategy',
        'terminal',
        'test',
        'vars',
    ]

    # most plugins follow a standard naming convention
    plugin_map = dict(('%s_plugins' % name, name) for name in plugin_list)

    # these plugins do not follow the standard naming convention
    plugin_map.update(
        doc_fragment='doc_fragments',
        library='modules',
        module_utils='module_utils',
    )

    env.update(dict(('ANSIBLE_%s' % key.upper(), os.path.join(plugin_root, value)) for key, value in plugin_map.items()))

    # only configure directories which exist
    env = dict((key, value) for key, value in env.items() if os.path.isdir(value))

    return env


@mutex
def get_ansible_bin_path(args: CommonConfig) -> str:
    """
    Return a directory usable for PATH, containing only the ansible entry points.
    If a temporary directory is required, it will be cached for the lifetime of the process and cleaned up at exit.
    """
    try:
        return get_ansible_bin_path.bin_path  # type: ignore[attr-defined]
    except AttributeError:
        pass

    if ANSIBLE_SOURCE_ROOT:
        # when running from source there is no need for a temporary directory since we already have known entry point scripts
        bin_path = os.path.join(ANSIBLE_ROOT, 'bin')
    else:
        # when not running from source the installed entry points cannot be relied upon
        # doing so would require using the interpreter specified by those entry points, which conflicts with using our interpreter and injector
        # instead a temporary directory is created which contains only ansible entry points
        # symbolic links cannot be used since the files are likely not executable
        bin_path = create_temp_dir(prefix='ansible-test-', suffix='-bin')
        bin_links = {os.path.join(bin_path, name): get_cli_path(path) for name, path in ANSIBLE_BIN_SYMLINK_MAP.items()}

        if not args.explain:
            for dst, src in bin_links.items():
                shutil.copy(src, dst)
                verified_chmod(dst, MODE_FILE_EXECUTE)

    get_ansible_bin_path.bin_path = bin_path  # type: ignore[attr-defined]

    return bin_path


def get_cli_path(path: str) -> str:
    """Return the absolute path to the CLI script from the given path which is relative to the `bin` directory of the original source tree layout."""
    path_rewrite = {
        '../lib/ansible/': ANSIBLE_LIB_ROOT,
        '../test/lib/ansible_test/': ANSIBLE_TEST_ROOT,
    }

    for prefix, destination in path_rewrite.items():
        if path.startswith(prefix):
            return os.path.join(destination, path[len(prefix):])

    raise RuntimeError(path)


# noinspection PyUnusedLocal
@mutex
def get_ansible_python_path(args: CommonConfig) -> str:
    """
    Return a directory usable for PYTHONPATH, containing only the ansible package.
    If a temporary directory is required, it will be cached for the lifetime of the process and cleaned up at exit.
    """
    del args  # not currently used

    try:
        return get_ansible_python_path.python_path  # type: ignore[attr-defined]
    except AttributeError:
        pass

    if ANSIBLE_SOURCE_ROOT:
        # when running from source there is no need for a temporary directory to isolate the ansible package
        python_path = os.path.dirname(ANSIBLE_LIB_ROOT)
    else:
        # when not running from source the installed directory is unsafe to add to PYTHONPATH
        # doing so would expose many unwanted packages on sys.path
        # instead a temporary directory is created which contains only ansible using a symlink
        python_path = create_temp_dir(prefix='ansible-test-')

        os.symlink(ANSIBLE_LIB_ROOT, os.path.join(python_path, 'ansible'))

    get_ansible_python_path.python_path = python_path  # type: ignore[attr-defined]

    return python_path


class CollectionDetail:
    """Collection detail."""

    def __init__(self) -> None:
        self.version: t.Optional[str] = None


class CollectionDetailError(ApplicationError):
    """An error occurred retrieving collection detail."""

    def __init__(self, reason: str) -> None:
        super().__init__('Error collecting collection detail: %s' % reason)
        self.reason = reason


def get_collection_detail(python: PythonConfig) -> CollectionDetail:
    """Return collection detail."""
    collection = data_context().content.collection
    directory = os.path.join(collection.root, collection.directory)

    stdout = raw_command([python.path, os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'collection_detail.py'), directory], capture=True)[0]
    result = json.loads(stdout)
    error = result.get('error')

    if error:
        raise CollectionDetailError(error)

    version = result.get('version')

    detail = CollectionDetail()
    detail.version = str(version) if version is not None else None

    return detail


def run_playbook(
    args: EnvironmentConfig,
    inventory_path: str,
    playbook: str,
    capture: bool,
    variables: t.Optional[dict[str, t.Any]] = None,
) -> None:
    """Run the specified playbook using the given inventory file and playbook variables."""
    playbook_path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'playbooks', playbook)
    cmd = ['ansible-playbook', '-i', inventory_path, playbook_path]

    if variables:
        cmd.extend(['-e', json.dumps(variables)])

    if args.verbosity:
        cmd.append('-%s' % ('v' * args.verbosity))

    install_requirements(args, args.controller_python, ansible=True)  # run_playbook()
    env = ansible_environment(args)
    intercept_python(args, args.controller_python, cmd, env, capture=capture)
