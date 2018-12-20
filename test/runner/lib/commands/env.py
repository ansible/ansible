"""Show information about the test environment."""

from __future__ import absolute_import, print_function

import datetime
import json
import os
import platform
import re
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

from lib.git import (
    Git,
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
            version=get_ansible_version(args),
        ),
        git=get_git_status(args),
        environ=os.environ.copy(),
        modules=get_modules(),
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
        display.info('git:')
        display.info('  commit: %s' % data['git']['commit'])
        display.info('  commit_range: %s' % data['git']['commit_range'])
        display.info('  merged_updates: %d entries' % len(data['git']['merged_updates']))
        display.info('environ: %d entries' % len(data['environ']))
        display.info('modules: %d modules' % len(data['modules']))

    if args.dump and not args.explain:
        with open('test/results/bot/data-environment.json', 'w') as results_fd:
            results_fd.write(json.dumps(data, sort_keys=True))


def get_modules():
    """
    :rtype: dict[str, str]
    """
    modules = dict((t.module, t.path) for t in walk_module_targets())

    return modules


def get_ansible_version(args):
    """
    :type args: EnvConfig
    :rtype: str | None
    """
    code = 'from __future__ import (print_function); from ansible.release import __version__; print(__version__)'
    cmd = [sys.executable, '-c', code]
    env = ansible_environment(args)

    try:
        ansible_version, _dummy = raw_command(cmd, env=env, capture=True)
        ansible_version = ansible_version.strip()
    except SubprocessError:
        ansible_version = None

    return ansible_version


def get_git_status(args):
    """
    :type args: EnvConfig
    :rtype: dict[str, any]
    """
    commit = os.environ.get('COMMIT')
    commit_range = os.environ.get('SHIPPABLE_COMMIT_RANGE')

    git_status = dict(
        commit=commit,
        commit_range=commit_range,
        merged_updates=get_merged_updates(args, commit),
    )

    return git_status


def get_merged_updates(args, commit):
    """
    :type args: CommonConfig
    :type commit: str
    :rtype: list[str]
    """
    if not commit:
        return []

    git = Git(args)

    rev_list = git.get_rev_list(['%s..HEAD' % commit])

    if not rev_list:
        return []

    last_rev = rev_list[0]
    last_change = git.run_git(['show', '--no-patch', last_rev])

    if len(rev_list) == 1:
        raise Exception('Found only one commit after %s when at least 2 were expected:\n\n%s' % (commit, last_change))

    if not re.search(r'^Merge: ', last_change):
        raise Exception('The last commit after %s does not appear to be a merge commit:\n\n%s' % (commit, last_change))

    return rev_list[1:]
