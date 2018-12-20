"""Show information about the test environment."""

from __future__ import absolute_import, print_function

import datetime
import json
import os
import platform
import re
import sys

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
        ansible=dict(
            version=get_ansible_version(args),
        ),
        environ=os.environ.copy(),
        git=get_git_status(args),
        platform=dict(
            datetime=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            platform=platform.platform(),
            uname=platform.uname(),
        ),
        python=dict(
            executable=sys.executable,
            path=sys.path,
            version=platform.python_version(),
        ),
    )

    if args.show:
        verbose = {
            'environ': 2,
            'platform.uname': 1,
            'python.path': 2,
        }

        show_dict(data, verbose)

    if args.dump and not args.explain:
        with open('test/results/bot/data-environment.json', 'w') as results_fd:
            results_fd.write(json.dumps(data, sort_keys=True))


def show_dict(data, verbose, root_verbosity=0, path=None):
    """
    :type data: dict[str, any]
    :type verbose: dict[str, int]
    :type root_verbosity: int
    :type path: list[str] | None
    """
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
            display.info(indent + '%s:' % key, verbosity=verbosity)
            show_dict(value, verbose, verbosity, key_path)
        else:
            display.info(indent + '%s: %s' % (key, value), verbosity=verbosity)


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
        merged_commits=get_merged_commits(args, commit),
        root=os.getcwd(),
    )

    return git_status


def get_merged_commits(args, commit):
    """
    :type args: CommonConfig
    :type commit: str
    :rtype: list[str] | None
    """
    if not commit:
        return None

    git = Git(args)

    rev_list = git.get_rev_list(['%s..HEAD' % commit])

    if not rev_list:
        return []

    last_rev = rev_list[0]
    last_change = git.run_git(['show', '--no-patch', last_rev])

    if len(rev_list) == 1:
        raise Exception('Found only one commit after %s when at least 2 were expected:\n\n%s' % (commit, last_change))

    if not re.search(r'^Merge: ', last_change, flags=re.MULTILINE):
        raise Exception('The last commit after %s does not appear to be a merge commit:\n\n%s' % (commit, last_change))

    return rev_list[1:]
