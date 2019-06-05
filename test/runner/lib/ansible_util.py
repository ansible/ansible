"""Miscellaneous utility functions and classes specific to ansible cli tools."""

from __future__ import absolute_import, print_function

import json
import os

from lib.constants import (
    SOFT_RLIMIT_NOFILE,
)

from lib.util import (
    common_environment,
    display,
    find_python,
    run_command,
    ApplicationError,
)

from lib.config import (
    IntegrationConfig,
    EnvironmentConfig,
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

    ansible_path = os.path.join(os.getcwd(), 'bin')

    if not path.startswith(ansible_path + os.path.pathsep):
        path = ansible_path + os.path.pathsep + path

    if ansible_config:
        pass
    elif isinstance(args, IntegrationConfig):
        ansible_config = 'test/integration/%s.cfg' % args.command
    else:
        ansible_config = 'test/%s/ansible.cfg' % args.command

    if not args.explain and not os.path.exists(ansible_config):
        raise ApplicationError('Configuration not found: %s' % ansible_config)

    ansible = dict(
        ANSIBLE_PYTHON_MODULE_RLIMIT_NOFILE=str(SOFT_RLIMIT_NOFILE),
        ANSIBLE_FORCE_COLOR='%s' % 'true' if args.color and color else 'false',
        ANSIBLE_DEPRECATION_WARNINGS='false',
        ANSIBLE_HOST_KEY_CHECKING='false',
        ANSIBLE_RETRY_FILES_ENABLED='false',
        ANSIBLE_CONFIG=os.path.abspath(ansible_config),
        ANSIBLE_LIBRARY='/dev/null',
        PYTHONPATH=os.path.abspath('lib'),
        PAGER='/bin/cat',
        PATH=path,
    )

    env.update(ansible)

    if args.debug:
        env.update(dict(
            ANSIBLE_DEBUG='true',
            ANSIBLE_LOG_PATH=os.path.abspath('test/results/logs/debug.log'),
        ))

    return env


def check_pyyaml(args, version):
    """
    :type args: EnvironmentConfig
    :type version: str
    """
    if version in CHECK_YAML_VERSIONS:
        return

    python = find_python(version)
    stdout, _dummy = run_command(args, [python, 'test/runner/yamlcheck.py'], capture=True)

    if args.explain:
        return

    CHECK_YAML_VERSIONS[version] = result = json.loads(stdout)

    yaml = result['yaml']
    cloader = result['cloader']

    if not yaml:
        display.warning('PyYAML is not installed for interpreter: %s' % python)
    elif not cloader:
        display.warning('PyYAML will be slow due to installation without libyaml support for interpreter: %s' % python)
