"""Show information about the test environment."""

from __future__ import absolute_import, print_function

import datetime
import json
import os
import platform
import sys

from lib.target import (
    walk_module_targets,
)

from lib.config import (
    CommonConfig,
)

from lib.util import (
    display,
    raw_command,
    SubprocessError,
)

from lib.ansible_util import (
    ansible_environment,
)


class EnvConfig(CommonConfig):
    """Configuration for the tools command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(EnvConfig, self).__init__(args, 'env')

        self.show = args.show or not args.dump
        self.dump = args.dump


def command_env(args):
    """
    :type args: EnvConfig
    """
    modules = dict((t.module, t.path) for t in walk_module_targets())

    code = 'from __future__ import (print_function); from ansible.release import __version__; print(__version__)'
    cmd = [sys.executable, '-c', code]
    env = ansible_environment(args)

    try:
        ansible_version, _dummy = raw_command(cmd, env=env, capture=True)
        ansible_version = ansible_version.strip()
    except SubprocessError:
        ansible_version = None

    data = dict(
        datetime=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        cwd=os.getcwd(),
        platform=dict(
            platform=platform.platform(),
            uname=platform.uname(),
        ),
        python=dict(
            version=platform.python_version(),
            executable=sys.executable,
            path=sys.path,
        ),
        ansible=dict(
            version=ansible_version,
        ),
        environ=os.environ.copy(),
        modules=modules,
    )

    if args.show:
        display.info('datetime: %s' % data['datetime'])
        display.info('cwd: %s' % data['cwd'])
        display.info('platform:')
        display.info('  platform: %s' % data['platform']['platform'])
        display.info('  uname: %s' % list(data['platform']['uname']))
        display.info('python:')
        display.info('  version: %s' % data['python']['version'])
        display.info('  executable: %s' % data['python']['executable'])
        display.info('  path: %d entries' % len(data['python']['path']))
        display.info('ansible:')
        display.info('  version: %s' % data['ansible']['version'])
        display.info('environ: %d entries' % len(data['environ']))
        display.info('modules: %d modules' % len(modules))

    if args.dump and not args.explain:
        with open('test/results/bot/data-environment.json', 'w') as results_fd:
            results_fd.write(json.dumps(data, sort_keys=True))
