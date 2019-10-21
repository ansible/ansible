"""Miscellaneous utility functions and classes specific to ansible cli tools."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os

from .constants import (
    SOFT_RLIMIT_NOFILE,
)

from .util import (
    common_environment,
    display,
    find_python,
    ApplicationError,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_BIN_PATH,
    ANSIBLE_SOURCE_ROOT,
)

from .util_common import (
    create_temp_dir,
    run_command,
    ResultType,
)

from .config import (
    PosixIntegrationConfig,
    EnvironmentConfig,
    CommonConfig,
)

from .data import (
    data_context,
)

CHECK_YAML_VERSIONS = {}


def ansible_environment(args, color=True, ansible_config=None):
    """
    :type args: CommonConfig
    :type color: bool
    :type ansible_config: str | None
    :rtype: dict[str, str]
    """
    env = common_environment()
    path = env['PATH']

    if not path.startswith(ANSIBLE_BIN_PATH + os.path.pathsep):
        path = ANSIBLE_BIN_PATH + os.path.pathsep + path

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
        PYTHONPATH=get_ansible_python_path(),
        PAGER='/bin/cat',
        PATH=path,
    )

    if isinstance(args, PosixIntegrationConfig):
        ansible.update(dict(
            ANSIBLE_PYTHON_INTERPRETER='/set/ansible_python_interpreter/in/inventory',  # force tests to set ansible_python_interpreter in inventory
        ))

    env.update(ansible)

    if args.debug:
        env.update(dict(
            ANSIBLE_DEBUG='true',
            ANSIBLE_LOG_PATH=os.path.join(ResultType.LOGS.name, 'debug.log'),
        ))

    if data_context().content.collection:
        env.update(dict(
            ANSIBLE_COLLECTIONS_PATHS=data_context().content.collection.root,
        ))

    return env


def get_ansible_python_path():  # type: () -> str
    """
    Return a directory usable for PYTHONPATH, containing only the ansible package.
    If a temporary directory is required, it will be cached for the lifetime of the process and cleaned up at exit.
    """
    if ANSIBLE_SOURCE_ROOT:
        # when running from source there is no need for a temporary directory to isolate the ansible package
        return os.path.dirname(ANSIBLE_LIB_ROOT)

    try:
        return get_ansible_python_path.python_path
    except AttributeError:
        pass

    python_path = create_temp_dir(prefix='ansible-test-')
    get_ansible_python_path.python_path = python_path

    os.symlink(ANSIBLE_LIB_ROOT, os.path.join(python_path, 'ansible'))

    return python_path


def check_pyyaml(args, version):
    """
    :type args: EnvironmentConfig
    :type version: str
    """
    if version in CHECK_YAML_VERSIONS:
        return

    python = find_python(version)
    stdout, _dummy = run_command(args, [python, os.path.join(ANSIBLE_TEST_DATA_ROOT, 'yamlcheck.py')], capture=True)

    if args.explain:
        return

    CHECK_YAML_VERSIONS[version] = result = json.loads(stdout)

    yaml = result['yaml']
    cloader = result['cloader']

    if not yaml:
        display.warning('PyYAML is not installed for interpreter: %s' % python)
    elif not cloader:
        display.warning('PyYAML will be slow due to installation without libyaml support for interpreter: %s' % python)
