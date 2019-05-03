"""Show information about the test environment."""

from __future__ import absolute_import, print_function

import datetime
import json
import functools
import os
import platform
import re
import signal
import sys
import time

from lib.config import (
    CommonConfig,
    TestConfig,
)

from lib.util import (
    display,
    find_executable,
    raw_command,
    SubprocessError,
    ApplicationError,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.git import (
    Git,
)

from lib.docker_util import (
    docker_info,
    docker_version
)

from lib.thread import (
    WrappedThread,
)

from lib.constants import (
    TIMEOUT_PATH,
)

from lib.test import (
    TestTimeout,
)


class EnvConfig(CommonConfig):
    """Configuration for the tools command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(EnvConfig, self).__init__(args, 'env')

        self.show = args.show
        self.dump = args.dump
        self.timeout = args.timeout


def command_env(args):
    """
    :type args: EnvConfig
    """
    show_dump_env(args)
    set_timeout(args)


def show_dump_env(args):
    """
    :type args: EnvConfig
    """
    if not args.show and not args.dump:
        return

    data = dict(
        ansible=dict(
            version=get_ansible_version(args),
        ),
        docker=get_docker_details(args),
        environ=os.environ.copy(),
        git=get_git_details(args),
        platform=dict(
            datetime=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            platform=platform.platform(),
            uname=platform.uname(),
        ),
        python=dict(
            executable=sys.executable,
            version=platform.python_version(),
        ),
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
        with open('test/results/bot/data-environment.json', 'w') as results_fd:
            results_fd.write(json.dumps(data, sort_keys=True))


def set_timeout(args):
    """
    :type args: EnvConfig
    """
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

        with open(TIMEOUT_PATH, 'w') as timeout_fd:
            json.dump(data, timeout_fd, indent=4, sort_keys=True)
    elif os.path.exists(TIMEOUT_PATH):
        os.remove(TIMEOUT_PATH)


def get_timeout():
    """
    :rtype: dict[str, any] | None
    """
    if not os.path.exists(TIMEOUT_PATH):
        return None

    with open(TIMEOUT_PATH, 'r') as timeout_fd:
        data = json.load(timeout_fd)

    data['deadline'] = datetime.datetime.strptime(data['deadline'], '%Y-%m-%dT%H:%M:%SZ')

    return data


def configure_timeout(args):
    """
    :type args: CommonConfig
    """
    if isinstance(args, TestConfig):
        configure_test_timeout(args)  # only tests are subject to the timeout


def configure_test_timeout(args):
    """
    :type args: TestConfig
    """
    timeout = get_timeout()

    if not timeout:
        return

    timeout_start = datetime.datetime.utcnow()
    timeout_duration = timeout['duration']
    timeout_deadline = timeout['deadline']
    timeout_remaining = timeout_deadline - timeout_start

    test_timeout = TestTimeout(timeout_duration)

    if timeout_remaining <= datetime.timedelta():
        test_timeout.write(args)

        raise ApplicationError('The %d minute test timeout expired %s ago at %s.' % (
            timeout_duration, timeout_remaining * -1, timeout_deadline))

    display.info('The %d minute test timeout expires in %s at %s.' % (
        timeout_duration, timeout_remaining, timeout_deadline), verbosity=1)

    def timeout_handler(_dummy1, _dummy2):
        """Runs when SIGUSR1 is received."""
        test_timeout.write(args)

        raise ApplicationError('Tests aborted after exceeding the %d minute time limit.' % timeout_duration)

    def timeout_waiter(timeout_seconds):
        """
        :type timeout_seconds: int
        """
        time.sleep(timeout_seconds)
        os.kill(os.getpid(), signal.SIGUSR1)

    signal.signal(signal.SIGUSR1, timeout_handler)

    instance = WrappedThread(functools.partial(timeout_waiter, timeout_remaining.seconds))
    instance.daemon = True
    instance.start()


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
            min_verbosity = min([verbosity] + [v for k, v in verbose.items() if k.startswith('%s.' % key)])
            display.info(indent + '%s:' % key, verbosity=min_verbosity)
            show_dict(value, verbose, verbosity, key_path)
        else:
            display.info(indent + '%s: %s' % (key, value), verbosity=verbosity)


def get_ansible_version(args):
    """
    :type args: CommonConfig
    :rtype: str | None
    """
    code = 'from __future__ import (print_function); from ansible.release import __version__; print(__version__)'
    cmd = [sys.executable, '-c', code]
    env = ansible_environment(args)

    try:
        ansible_version, _dummy = raw_command(cmd, env=env, capture=True)
        ansible_version = ansible_version.strip()
    except SubprocessError as ex:
        display.warning('Unable to get Ansible version:\n%s' % ex)
        ansible_version = None

    return ansible_version


def get_docker_details(args):
    """
    :type args: CommonConfig
    :rtype: dict[str, any]
    """
    docker = find_executable('docker', required=False)
    info = None
    version = None

    if docker:
        try:
            info = docker_info(args)
        except SubprocessError as ex:
            display.warning('Failed to collect docker info:\n%s' % ex)

        try:
            version = docker_version(args)
        except SubprocessError as ex:
            display.warning('Failed to collect docker version:\n%s' % ex)

    docker_details = dict(
        executable=docker,
        info=info,
        version=version,
    )

    return docker_details


def get_git_details(args):
    """
    :type args: CommonConfig
    :rtype: dict[str, any]
    """
    commit = os.environ.get('COMMIT')
    base_commit = os.environ.get('BASE_COMMIT')

    git_details = dict(
        base_commit=base_commit,
        commit=commit,
        merged_commit=get_merged_commit(args, commit),
        root=os.getcwd(),
    )

    return git_details


def get_merged_commit(args, commit):
    """
    :type args: CommonConfig
    :type commit: str
    :rtype: str | None
    """
    if not commit:
        return None

    git = Git(args)

    try:
        show_commit = git.run_git(['show', '--no-patch', '--no-abbrev', commit])
    except SubprocessError as ex:
        # This should only fail for pull requests where the commit does not exist.
        # Merge runs would fail much earlier when attempting to checkout the commit.
        raise ApplicationError('Commit %s was not found:\n\n%s\n\n'
                               'GitHub may not have fully replicated the commit across their infrastructure.\n'
                               'It is also possible the commit was removed by a force push between job creation and execution.\n'
                               'Find the latest run for the pull request and restart failed jobs as needed.'
                               % (commit, ex.stderr.strip()))

    head_commit = git.run_git(['show', '--no-patch', '--no-abbrev', 'HEAD'])

    if show_commit == head_commit:
        # Commit is HEAD, so this is not a pull request or the base branch for the pull request is up-to-date.
        return None

    match_merge = re.search(r'^Merge: (?P<parents>[0-9a-f]{40} [0-9a-f]{40})$', head_commit, flags=re.MULTILINE)

    if not match_merge:
        # The most likely scenarios resulting in a failure here are:
        # A new run should or does supersede this job, but it wasn't cancelled in time.
        # A job was superseded and then later restarted.
        raise ApplicationError('HEAD is not commit %s or a merge commit:\n\n%s\n\n'
                               'This job has likely been superseded by another run due to additional commits being pushed.\n'
                               'Find the latest run for the pull request and restart failed jobs as needed.'
                               % (commit, head_commit.strip()))

    parents = set(match_merge.group('parents').split(' '))

    if len(parents) != 2:
        raise ApplicationError('HEAD is a %d-way octopus merge.' % len(parents))

    if commit not in parents:
        raise ApplicationError('Commit %s is not a parent of HEAD.' % commit)

    parents.remove(commit)

    last_commit = parents.pop()

    return last_commit
