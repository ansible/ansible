"""Execute Ansible sanity tests."""

from __future__ import absolute_import, print_function

import glob
import json
import os
import re

from xml.etree.ElementTree import (
    fromstring,
    Element,
)

from lib.util import (
    ApplicationError,
    SubprocessError,
    display,
    run_command,
    deepest_path,
    parse_to_dict,
    remove_tree,
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
    intercept_command,
    generate_pip_install,
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    TestSuccess,
    TestFailure,
    TestSkipped,
    TestMessage,
    calculate_best_confidence,
)

COMMAND = 'sanity'

PEP8_SKIP_PATH = 'test/sanity/pep8/skip.txt'
PEP8_LEGACY_PATH = 'test/sanity/pep8/legacy-files.txt'

PYLINT_SKIP_PATH = 'test/sanity/pylint/skip.txt'


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

    tests = sanity_get_tests()

    if args.test:
        tests = [t for t in tests if t.name in args.test]

    if args.skip_test:
        tests = [t for t in tests if t.name not in args.skip_test]

    total = 0
    failed = []

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

            options = ''

            if test.script:
                result = test.func(args, targets, test.script)
            elif test.intercept:
                result = test.func(args, targets, python_version=version)
                options = ' --python %s' % version
            else:
                result = test.func(args, targets)

            result.write(args)

            total += 1

            if isinstance(result, SanityFailure):
                failed.append(result.test + options)

    if failed:
        message = 'The %d sanity test(s) listed below (out of %d) failed. See error output above for details.\n%s' % (
            len(failed), total, '\n'.join(failed))

        if args.failure_ok:
            display.error(message)
        else:
            raise ApplicationError(message)


def command_sanity_code_smell(args, _, script):
    """
    :type args: SanityConfig
    :type _: SanityTargets
    :type script: str
    :rtype: SanityResult
    """
    test = os.path.splitext(os.path.basename(script))[0]

    cmd = [script]
    env = ansible_environment(args, color=False)

    try:
        stdout, stderr = run_command(args, cmd, env=env, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status:
        summary = str(SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout))
        return SanityFailure(test, summary=summary)

    return SanitySuccess(test)


def command_sanity_validate_modules(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'validate-modules'
    env = ansible_environment(args, color=False)

    paths = [deepest_path(i.path, 'lib/ansible/modules/') for i in targets.include_external]
    paths = sorted(set(p for p in paths if p))

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'test/sanity/validate-modules/validate-modules',
        '--format', 'json',
    ] + paths

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

    try:
        stdout, stderr = run_command(args, cmd, env=env, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status not in (0, 3):
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    messages = json.loads(stdout)

    results = []

    for filename in messages:
        output = messages[filename]

        for item in output['errors']:
            results.append(SanityMessage(
                path=filename,
                line=int(item['line']) if 'line' in item else 0,
                column=int(item['column']) if 'column' in item else 0,
                level='error',
                code='E%s' % item['code'],
                message=item['msg'],
            ))

    if results:
        return SanityFailure(test, messages=results)

    return SanitySuccess(test)


def command_sanity_shellcheck(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'shellcheck'

    with open('test/sanity/shellcheck/skip.txt', 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    with open('test/sanity/shellcheck/exclude.txt', 'r') as exclude_fd:
        exclude = set(exclude_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh' and i.path not in skip_paths)

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'shellcheck',
        '-e', ','.join(sorted(exclude)),
        '--format', 'checkstyle',
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status > 1:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    # json output is missing file paths in older versions of shellcheck, so we'll use xml instead
    root = fromstring(stdout)  # type: Element

    results = []

    for item in root:  # type: Element
        for entry in item:  # type: Element
            results.append(SanityMessage(
                message=entry.attrib['message'],
                path=item.attrib['name'],
                line=int(entry.attrib['line']),
                column=int(entry.attrib['column']),
                level=entry.attrib['severity'],
                code=entry.attrib['source'].replace('ShellCheck.', ''),
            ))

    if results:
        return SanityFailure(test, messages=results)

    return SanitySuccess(test)


def command_sanity_pep8(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'pep8'

    with open(PEP8_SKIP_PATH, 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    with open(PEP8_LEGACY_PATH, 'r') as legacy_fd:
        legacy_paths = legacy_fd.read().splitlines()

    with open('test/sanity/pep8/legacy-ignore.txt', 'r') as ignore_fd:
        legacy_ignore = set(ignore_fd.read().splitlines())

    with open('test/sanity/pep8/current-ignore.txt', 'r') as ignore_fd:
        current_ignore = sorted(ignore_fd.read().splitlines())

    skip_paths_set = set(skip_paths)
    legacy_paths_set = set(legacy_paths)

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and i.path not in skip_paths_set)

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'pycodestyle',
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
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[WE][0-9]{3}) (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    results = [SanityMessage(
        message=r['message'],
        path=r['path'],
        line=int(r['line']),
        column=int(r['column']),
        level='warning' if r['code'].startswith('W') else 'error',
        code=r['code'],
    ) for r in results]

    failed_result_paths = set([result.path for result in results])
    used_paths = set(paths)

    errors = []
    summary = {}

    line = 0

    for path in legacy_paths:
        line += 1

        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append(SanityMessage(
                code='A101',
                message='Remove "%s" since it does not exist' % path,
                path=PEP8_LEGACY_PATH,
                line=line,
                column=1,
                confidence=calculate_best_confidence(((PEP8_LEGACY_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
            ))

        if path in used_paths and path not in failed_result_paths:
            # Keep files out of the list which no longer require the relaxed rule set.
            errors.append(SanityMessage(
                code='A201',
                message='Remove "%s" since it passes the current rule set' % path,
                path=PEP8_LEGACY_PATH,
                line=line,
                column=1,
                confidence=calculate_best_confidence(((PEP8_LEGACY_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
            ))

    line = 0

    for path in skip_paths:
        line += 1

        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append(SanityMessage(
                code='A101',
                message='Remove "%s" since it does not exist' % path,
                path=PEP8_SKIP_PATH,
                line=line,
                column=1,
                confidence=calculate_best_confidence(((PEP8_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
            ))

    for result in results:
        if result.path in legacy_paths_set and result.code in legacy_ignore:
            # Files on the legacy list are permitted to have errors on the legacy ignore list.
            # However, we want to report on their existence to track progress towards eliminating these exceptions.
            display.info('PEP 8: %s (legacy)' % result, verbosity=3)

            key = '%s %s' % (result.code, re.sub('[0-9]+', 'NNN', result.message))

            if key not in summary:
                summary[key] = 0

            summary[key] += 1
        else:
            # Files not on the legacy list and errors not on the legacy ignore list are PEP 8 policy errors.
            errors.append(result)

    if summary:
        lines = []
        count = 0

        for key in sorted(summary):
            count += summary[key]
            lines.append('PEP 8: %5d %s' % (summary[key], key))

        display.info('PEP 8: There were %d different legacy issues found (%d total):' % (len(summary), count), verbosity=1)
        display.info('PEP 8: Count Code Message', verbosity=1)

        for line in lines:
            display.info(line, verbosity=1)

    if errors:
        return SanityFailure(test, messages=errors)

    return SanitySuccess(test)


def command_sanity_pylint(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'pylint'

    with open(PYLINT_SKIP_PATH, 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    with open('test/sanity/pylint/disable.txt', 'r') as disable_fd:
        disable = set(c for c in disable_fd.read().splitlines() if not c.strip().startswith('#'))

    with open('test/sanity/pylint/enable.txt', 'r') as enable_fd:
        enable = set(c for c in enable_fd.read().splitlines() if not c.strip().startswith('#'))

    skip_paths_set = set(skip_paths)

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and i.path not in skip_paths_set)

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'pylint',
        '--jobs', '0',
        '--reports', 'n',
        '--max-line-length', '160',
        '--rcfile', '/dev/null',
        '--ignored-modules', '_MovedItems',
        '--output-format', 'json',
        '--disable', ','.join(sorted(disable)),
        '--enable', ','.join(sorted(enable)),
    ] + paths

    env = ansible_environment(args)

    try:
        stdout, stderr = run_command(args, cmd, env=env, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status >= 32:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    if stdout:
        messages = json.loads(stdout)
    else:
        messages = []

    errors = [SanityMessage(
        message=m['message'],
        path=m['path'],
        line=int(m['line']),
        column=int(m['column']),
        level=m['type'],
        code=m['symbol'],
    ) for m in messages]

    line = 0

    for path in skip_paths:
        line += 1

        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append(SanityMessage(
                code='A101',
                message='Remove "%s" since it does not exist' % path,
                path=PYLINT_SKIP_PATH,
                line=line,
                column=1,
                confidence=calculate_best_confidence(((PYLINT_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
            ))

    if errors:
        return SanityFailure(test, messages=errors)

    return SanitySuccess(test)


def command_sanity_yamllint(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'yamllint'

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml'))

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'yamllint',
        '--format', 'parsable',
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): \[(?P<level>warning|error)\] (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    results = [SanityMessage(
        message=r['message'],
        path=r['path'],
        line=int(r['line']),
        column=int(r['column']),
        level=r['level'],
    ) for r in results]

    if results:
        return SanityFailure(test, messages=results)

    return SanitySuccess(test)


def command_sanity_rstcheck(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'rstcheck'

    with open('test/sanity/rstcheck/ignore-substitutions.txt', 'r') as ignore_fd:
        ignore_substitutions = sorted(set(ignore_fd.read().splitlines()))

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.rst',))

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'rstcheck',
        '--report', 'warning',
        '--ignore-substitutions', ','.join(ignore_substitutions),
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stdout:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+): \((?P<level>INFO|WARNING|ERROR|SEVERE)/[0-4]\) (?P<message>.*)$'

    results = [parse_to_dict(pattern, line) for line in stderr.splitlines()]

    results = [SanityMessage(
        message=r['message'],
        path=r['path'],
        line=int(r['line']),
        column=0,
        level=r['level'],
    ) for r in results]

    if results:
        return SanityFailure(test, messages=results)

    return SanitySuccess(test)


# noinspection PyUnusedLocal
def command_sanity_sanity_docs(args, targets):  # pylint: disable=locally-disabled, unused-argument
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'sanity-docs'

    sanity_dir = 'docs/docsite/rst/dev_guide/testing/sanity'
    sanity_docs = set(part[0] for part in (os.path.splitext(name) for name in os.listdir(sanity_dir)) if part[1] == '.rst')
    sanity_tests = set(sanity_test.name for sanity_test in sanity_get_tests())

    missing = sanity_tests - sanity_docs

    results = []

    results += [SanityMessage(
        message='missing docs for ansible-test sanity --test %s' % r,
        path=os.path.join(sanity_dir, '%s.rst' % r),
    ) for r in sorted(missing)]

    if results:
        return SanityFailure(test, messages=results)

    return SanitySuccess(test)


def command_sanity_ansible_doc(args, targets, python_version):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :type python_version: str
    :rtype: SanityResult
    """
    test = 'ansible-doc'

    with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
        skip_modules = set(skip_fd.read().splitlines())

    modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                     set(m for i in targets.exclude_external for m in i.modules) -
                     skip_modules)

    if not modules:
        return SanitySkipped(test, python_version=python_version)

    env = ansible_environment(args, color=False)
    cmd = ['ansible-doc'] + modules

    try:
        stdout, stderr = intercept_command(args, cmd, target_name='ansible-doc', env=env, capture=True, python_version=python_version)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if status:
        summary = str(SubprocessError(cmd=cmd, status=status, stderr=stderr))
        return SanityFailure(test, summary=summary, python_version=python_version)

    if stdout:
        display.info(stdout.strip(), verbosity=3)

    if stderr:
        summary = 'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
        return SanityFailure(test, summary=summary, python_version=python_version)

    return SanitySuccess(test, python_version=python_version)


def command_sanity_import(args, targets, python_version):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :type python_version: str
    :rtype: SanityResult
    """
    test = 'import'

    with open('test/sanity/import/skip.txt', 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    skip_paths_set = set(skip_paths)

    paths = sorted(
        i.path
        for i in targets.include
        if os.path.splitext(i.path)[1] == '.py' and
        (i.path.startswith('lib/ansible/modules/') or i.path.startswith('lib/ansible/module_utils/')) and
        i.path not in skip_paths_set
    )

    if not paths:
        return SanitySkipped(test, python_version=python_version)

    env = ansible_environment(args, color=False)

    # create a clean virtual environment to minimize the available imports beyond the python standard library
    virtual_environment_path = os.path.abspath('test/runner/.tox/minimal-py%s' % python_version.replace('.', ''))
    virtual_environment_bin = os.path.join(virtual_environment_path, 'bin')

    remove_tree(virtual_environment_path)

    cmd = ['virtualenv', virtual_environment_path, '--python', 'python%s' % python_version, '--no-setuptools', '--no-wheel']

    if not args.coverage:
        cmd.append('--no-pip')

    run_command(args, cmd, capture=True)

    # add the importer to our virtual environment so it can be accessed through the coverage injector
    importer_path = os.path.join(virtual_environment_bin, 'importer.py')
    os.symlink(os.path.abspath('test/runner/importer.py'), importer_path)

    # activate the virtual environment
    env['PATH'] = '%s:%s' % (virtual_environment_bin, env['PATH'])
    env['PYTHONPATH'] = os.path.abspath('test/runner/import/lib')

    # make sure coverage is available in the virtual environment if needed
    if args.coverage:
        run_command(args, generate_pip_install('sanity.import', packages=['coverage']), env=env)
        run_command(args, ['pip', 'uninstall', '--disable-pip-version-check', '-y', 'pip'], env=env)

    cmd = ['importer.py'] + paths

    results = []

    try:
        stdout, stderr = intercept_command(args, cmd, target_name=test, env=env, capture=True, python_version=python_version, path=env['PATH'])

        if stdout or stderr:
            raise SubprocessError(cmd, stdout=stdout, stderr=stderr)
    except SubprocessError as ex:
        if ex.status != 10 or ex.stderr or not ex.stdout:
            raise

        pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

        results = [re.search(pattern, line).groupdict() for line in ex.stdout.splitlines()]

        results = [SanityMessage(
            message=r['message'],
            path=r['path'],
            line=int(r['line']),
            column=int(r['column']),
        ) for r in results]

        results = [result for result in results if result.path not in skip_paths]

    if results:
        return SanityFailure(test, messages=results, python_version=python_version)

    return SanitySuccess(test, python_version=python_version)


def collect_code_smell_tests():
    """
    :rtype: tuple(SanityFunc)
    """
    with open('test/sanity/code-smell/skip.txt', 'r') as skip_fd:
        skip_tests = skip_fd.read().splitlines()

    paths = glob.glob('test/sanity/code-smell/*')
    paths = sorted(p for p in paths if os.access(p, os.X_OK) and os.path.isfile(p) and os.path.basename(p) not in skip_tests)

    tests = tuple(SanityFunc(os.path.splitext(os.path.basename(p))[0], command_sanity_code_smell, script=p, intercept=False) for p in paths)

    return tests


def sanity_get_tests():
    """
    :rtype: tuple(SanityFunc)
    """
    return SANITY_TESTS


class SanitySuccess(TestSuccess):
    """Sanity test success."""
    def __init__(self, test, python_version=None):
        """
        :type test: str
        :type python_version: str
        """
        super(SanitySuccess, self).__init__(COMMAND, test, python_version)


class SanitySkipped(TestSkipped):
    """Sanity test skipped."""
    def __init__(self, test, python_version=None):
        """
        :type test: str
        :type python_version: str
        """
        super(SanitySkipped, self).__init__(COMMAND, test, python_version)


class SanityFailure(TestFailure):
    """Sanity test failure."""
    def __init__(self, test, python_version=None, messages=None, summary=None):
        """
        :type test: str
        :type python_version: str
        :type messages: list[SanityMessage]
        :type summary: str
        """
        super(SanityFailure, self).__init__(COMMAND, test, python_version, messages, summary)


class SanityMessage(TestMessage):
    """Single sanity test message for one file."""
    pass


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
    def __init__(self, name, func, intercept=True, script=None):
        """
        :type name: str
        :type func: (SanityConfig, SanityTargets) -> SanityResult
        :type intercept: bool
        :type script: str | None
        """
        super(SanityFunc, self).__init__(name)

        self.func = func
        self.intercept = intercept
        self.script = script


SANITY_TESTS = (
    SanityFunc('shellcheck', command_sanity_shellcheck, intercept=False),
    SanityFunc('pep8', command_sanity_pep8, intercept=False),
    SanityFunc('pylint', command_sanity_pylint, intercept=False),
    SanityFunc('yamllint', command_sanity_yamllint, intercept=False),
    SanityFunc('rstcheck', command_sanity_rstcheck, intercept=False),
    SanityFunc('sanity-docs', command_sanity_sanity_docs, intercept=False),
    SanityFunc('validate-modules', command_sanity_validate_modules, intercept=False),
    SanityFunc('ansible-doc', command_sanity_ansible_doc),
    SanityFunc('import', command_sanity_import),
)


def sanity_init():
    """Initialize full sanity test list (includes code-smell scripts determined at runtime)."""
    global SANITY_TESTS  # pylint: disable=locally-disabled, global-statement
    SANITY_TESTS = tuple(sorted(SANITY_TESTS + collect_code_smell_tests(), key=lambda k: k.name))
