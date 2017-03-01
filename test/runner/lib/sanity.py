"""Execute Ansible sanity tests."""

from __future__ import absolute_import, print_function

import glob
import os
import re

from lib.util import (
    ApplicationError,
    SubprocessError,
    MissingEnvironmentVariable,
    display,
    run_command,
    deepest_path,
    is_shippable,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.target import (
    walk_external_targets,
    walk_internal_targets,
    walk_sanity_targets,
)

from lib.executor import (
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
    install_command_requirements,
    SUPPORTED_PYTHON_VERSIONS,
    TestConfig,
    intercept_command,
)


def command_sanity(args):
    """
    :type args: SanityConfig
    """
    changes = get_changes_filter(args)
    require = (args.require or []) + changes
    targets = SanityTargets(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes)

    install_command_requirements(args)

    tests = SANITY_TESTS

    if args.test:
        tests = [t for t in tests if t.name in args.test]

    if args.skip_test:
        tests = [t for t in tests if t.name not in args.skip_test]

    for test in tests:
        if args.list_tests:
            display.info(test.name)
            continue

        if test.intercept:
            versions = SUPPORTED_PYTHON_VERSIONS
        else:
            versions = None,

        for version in versions:
            if args.python and version and version != args.python:
                continue

            display.info('Sanity check using %s%s' % (test.name, ' with Python %s' % version if version else ''))

            if test.intercept:
                test.func(args, targets, python_version=version)
            else:
                test.func(args, targets)


def command_sanity_code_smell(args, _):
    """
    :type args: SanityConfig
    :type _: SanityTargets
    """
    with open('test/sanity/code-smell/skip.txt', 'r') as skip_fd:
        skip_tests = skip_fd.read().splitlines()

    tests = glob.glob('test/sanity/code-smell/*')
    tests = sorted(p for p in tests
                   if os.access(p, os.X_OK)
                   and os.path.isfile(p)
                   and os.path.basename(p) not in skip_tests)

    for test in tests:
        display.info('Code smell check using %s' % os.path.basename(test))
        run_command(args, [test])


def command_sanity_validate_modules(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    env = ansible_environment(args)

    paths = [deepest_path(i.path, 'lib/ansible/modules/') for i in targets.include_external]
    paths = sorted(set(p for p in paths if p))

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    cmd = ['test/sanity/validate-modules/validate-modules'] + paths

    with open('test/sanity/validate-modules/skip.txt', 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    skip_paths += [e.path for e in targets.exclude_external]

    if skip_paths:
        cmd += ['--exclude', '^(%s)' % '|'.join(skip_paths)]

    if args.base_branch:
        cmd.extend([
            '--base-branch', args.base_branch,
        ])
    else:
        display.warning('Cannot perform module comparison against the base branch. Base branch not detected when running locally.')

    run_command(args, cmd, env=env)


def command_sanity_shellcheck(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    with open('test/sanity/shellcheck/skip.txt', 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    with open('test/sanity/shellcheck/exclude.txt', 'r') as exclude_fd:
        exclude = set(exclude_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh' and i.path not in skip_paths)

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    run_command(args, ['shellcheck', '-e', ','.join(sorted(exclude))] + paths)


def command_sanity_pep8(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    skip_path = 'test/sanity/pep8/skip.txt'
    legacy_path = 'test/sanity/pep8/legacy-files.txt'

    with open(skip_path, 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    with open(legacy_path, 'r') as legacy_fd:
        legacy_paths = set(legacy_fd.read().splitlines())

    with open('test/sanity/pep8/legacy-ignore.txt', 'r') as ignore_fd:
        legacy_ignore = set(ignore_fd.read().splitlines())

    with open('test/sanity/pep8/current-ignore.txt', 'r') as ignore_fd:
        current_ignore = sorted(ignore_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and i.path not in skip_paths)

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    cmd = [
        'pep8',
        '--max-line-length', '160',
        '--config', '/dev/null',
        '--ignore', ','.join(sorted(current_ignore)),
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr)

    if args.explain:
        return

    pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[A-Z0-9]{4}) (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    for result in results:
        for key in 'line', 'column':
            result[key] = int(result[key])

    failed_result_paths = set([result['path'] for result in results])
    passed_legacy_paths = set([path for path in paths if path in legacy_paths and path not in failed_result_paths])

    errors = []
    summary = {}

    for path in sorted(passed_legacy_paths):
        # Keep files out of the list which no longer require the relaxed rule set.
        errors.append('PEP 8: %s: Passes current rule set. Remove from legacy list (%s).' % (path, legacy_path))

    for path in sorted(skip_paths):
        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append('PEP 8: %s: Does not exist. Remove from skip list (%s).' % (path, skip_path))

    for path in sorted(legacy_paths):
        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append('PEP 8: %s: Does not exist. Remove from legacy list (%s).' % (path, legacy_path))

    for result in results:
        path = result['path']
        line = result['line']
        column = result['column']
        code = result['code']
        message = result['message']

        msg = 'PEP 8: %s:%s:%s: %s %s' % (path, line, column, code, message)

        if path in legacy_paths:
            msg += ' (legacy)'
        else:
            msg += ' (current)'

        if path in legacy_paths and code in legacy_ignore:
            # Files on the legacy list are permitted to have errors on the legacy ignore list.
            # However, we want to report on their existence to track progress towards eliminating these exceptions.
            display.info(msg, verbosity=3)

            key = '%s %s' % (code, re.sub('[0-9]+', 'NNN', message))

            if key not in summary:
                summary[key] = 0

            summary[key] += 1
        else:
            # Files not on the legacy list and errors not on the legacy ignore list are PEP 8 policy errors.
            errors.append(msg)

    for error in errors:
        display.error(error)

    if summary:
        lines = []
        count = 0

        for key in sorted(summary):
            count += summary[key]
            lines.append('PEP 8: %5d %s' % (summary[key], key))

        display.info('PEP 8: There were %d different legacy issues found (%d total):' %
                     (len(summary), count), verbosity=1)

        display.info('PEP 8: Count Code Message', verbosity=1)

        for line in lines:
            display.info(line, verbosity=1)

    if errors:
        raise ApplicationError('PEP 8: There are %d issues which need to be resolved.' % len(errors))


def command_sanity_yamllint(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml'))

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    run_command(args, ['yamllint'] + paths)


def command_sanity_ansible_doc(args, targets, python_version):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :type python_version: str
    """
    with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
        skip_modules = set(skip_fd.read().splitlines())

    modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                     set(m for i in targets.exclude_external for m in i.modules) -
                     skip_modules)

    if not modules:
        display.info('No tests applicable.', verbosity=1)
        return

    env = ansible_environment(args)
    cmd = ['ansible-doc'] + modules

    stdout, stderr = intercept_command(args, cmd, env=env, capture=True, python_version=python_version)

    if stderr:
        display.error('Output on stderr from ansible-doc is considered an error.')
        raise SubprocessError(cmd, stderr=stderr)

    if stdout:
        display.info(stdout.strip(), verbosity=3)


class SanityTargets(object):
    """Sanity test target information."""
    def __init__(self, include, exclude, require):
        """
        :type include: list[str]
        :type exclude: list[str]
        :type require: list[str]
        """
        self.all = not include
        self.targets = tuple(sorted(walk_sanity_targets()))
        self.include = walk_internal_targets(self.targets, include, exclude, require)
        self.include_external, self.exclude_external = walk_external_targets(self.targets, include, exclude, require)


class SanityTest(object):
    """Sanity test base class."""
    def __init__(self, name):
        self.name = name


class SanityFunc(SanityTest):
    """Sanity test function information."""
    def __init__(self, name, func, intercept=True):
        """
        :type name: str
        :type func: (SanityConfig, SanityTargets) -> None
        :type intercept: bool
        """
        super(SanityFunc, self).__init__(name)

        self.func = func
        self.intercept = intercept


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(SanityConfig, self).__init__(args, 'sanity')

        self.test = args.test  # type: list [str]
        self.skip_test = args.skip_test  # type: list [str]
        self.list_tests = args.list_tests  # type: bool

        if args.base_branch:
            self.base_branch = args.base_branch  # str
        elif is_shippable():
            try:
                self.base_branch = os.environ['BASE_BRANCH']  # str
            except KeyError as ex:
                raise MissingEnvironmentVariable(name=ex.args[0])
        else:
            self.base_branch = ''


SANITY_TESTS = (
    # tests which ignore include/exclude (they're so fast it doesn't matter)
    SanityFunc('code-smell', command_sanity_code_smell, intercept=False),
    # tests which honor include/exclude
    SanityFunc('shellcheck', command_sanity_shellcheck, intercept=False),
    SanityFunc('pep8', command_sanity_pep8, intercept=False),
    SanityFunc('yamllint', command_sanity_yamllint, intercept=False),
    SanityFunc('validate-modules', command_sanity_validate_modules, intercept=False),
    SanityFunc('ansible-doc', command_sanity_ansible_doc),
)
