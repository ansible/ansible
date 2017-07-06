"""Miscellaneous utility functions and classes specific to ansible cli tools."""

from __future__ import absolute_import, print_function

import os

from lib.util import common_environment
from lib.config import IntegrationConfig

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

    ansible = dict(
        ANSIBLE_FORCE_COLOR='%s' % 'true' if args.color and color else 'false',
        ANSIBLE_DEPRECATION_WARNINGS='false',
        ANSIBLE_CONFIG='/dev/null',
        ANSIBLE_HOST_KEY_CHECKING='false',
        PYTHONPATH=os.path.abspath('lib'),
        PAGER='/bin/cat',
        PATH=path,
    )

    env.update(ansible)

    if args.debug:
        env.update(dict(ANSIBLE_DEBUG='true'))

    if isinstance(args, IntegrationConfig):
        if args.debug_strategy:
            env.update(dict(ANSIBLE_STRATEGY='debug'))

    return env
