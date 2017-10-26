"""Miscellaneous utility functions and classes specific to ansible cli tools."""

from __future__ import absolute_import, print_function

import os

from lib.util import (
    common_environment,
    ApplicationError,
)

from lib.config import (
    IntegrationConfig,
)


def ansible_environment(args, color=True):
    """
    :type args: CommonConfig
    :type color: bool
    :rtype: dict[str, str]
    """
    env = common_environment()
    path = env['PATH']

    ansible_path = os.path.join(os.getcwd(), 'bin')

    if not path.startswith(ansible_path + os.pathsep):
        path = ansible_path + os.pathsep + path

    if isinstance(args, IntegrationConfig):
        ansible_config = 'test/integration/%s.cfg' % args.command
    else:
        ansible_config = 'test/%s/ansible.cfg' % args.command

    if not os.path.exists(ansible_config):
        raise ApplicationError('Configuration not found: %s' % ansible_config)

    ansible = dict(
        ANSIBLE_FORCE_COLOR='%s' % 'true' if args.color and color else 'false',
        ANSIBLE_DEPRECATION_WARNINGS='false',
        ANSIBLE_HOST_KEY_CHECKING='false',
        ANSIBLE_CONFIG=os.path.abspath(ansible_config),
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
