"""Execute Ansible sanity tests."""
from __future__ import absolute_import, print_function

import abc
import glob
import os
import re

from lib.util import (
    ApplicationError,
    SubprocessError,
    display,
    run_command,
    import_plugins,
    load_plugins,
    ABC,
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
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    TestSuccess,
    TestFailure,
    TestSkipped,
    TestMessage,
)

COMMAND = 'sanity'


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

        if isinstance(test, SanityMultipleVersion):
            versions = SUPPORTED_PYTHON_VERSIONS
        else:
            versions = (None,)

        for version in versions:
            if args.python and version and version != args.python_version:
                continue

            display.info('Sanity check using %s%s' % (test.name, ' with Python %s' % version if version else ''))

            options = ''

            if isinstance(test, SanityCodeSmellTest):
                result = test.test(args)
            elif isinstance(test, SanityMultipleVersion):
                result = test.test(args, targets, python_version=version)
                options = ' --python %s' % version
            elif isinstance(test, SanitySingleVersion):
                result = test.test(args, targets)
            else:
                raise Exception('Unsupported test type: %s' % type(test))

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


def collect_code_smell_tests():
    """
    :rtype: tuple[SanityCodeSmellTest]
    """
    with open('test/sanity/code-smell/skip.txt', 'r') as skip_fd:
        skip_tests = skip_fd.read().splitlines()

    paths = glob.glob('test/sanity/code-smell/*')
    paths = sorted(p for p in paths if os.access(p, os.X_OK) and os.path.isfile(p) and os.path.basename(p) not in skip_tests)

    tests = tuple(SanityCodeSmellTest(p) for p in paths)

    return tests


def sanity_get_tests():
    """
    :rtype: tuple[SanityFunc]
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
        :type summary: unicode
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


class SanityTest(ABC):
    """Sanity test base class."""
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self.name = name


class SanityCodeSmellTest(SanityTest):
    """Sanity test script."""
    def __init__(self, path):
        name = os.path.splitext(os.path.basename(path))[0]

        self.path = path

        super(SanityCodeSmellTest, self).__init__(name)

    def test(self, args):
        """
        :type args: SanityConfig
        :rtype: SanityResult
        """
        cmd = [self.path]
        env = ansible_environment(args, color=False)

        try:
            stdout, stderr = run_command(args, cmd, env=env, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr or status:
            summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
            return SanityFailure(self.name, summary=summary)

        return SanitySuccess(self.name)


class SanityFunc(SanityTest):
    """Base class for sanity test plugins."""
    def __init__(self):
        name = self.__class__.__name__
        name = re.sub(r'Test$', '', name)  # drop Test suffix
        name = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', name).lower()  # use dashes instead of capitalization

        super(SanityFunc, self).__init__(name)


class SanitySingleVersion(SanityFunc):
    """Base class for sanity test plugins which should run on a single python version."""
    @abc.abstractmethod
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: SanityResult
        """
        pass


class SanityMultipleVersion(SanityFunc):
    """Base class for sanity test plugins which should run on multiple python versions."""
    @abc.abstractmethod
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: SanityResult
        """
        pass


SANITY_TESTS = (
)


def sanity_init():
    """Initialize full sanity test list (includes code-smell scripts determined at runtime)."""
    import_plugins('sanity')
    sanity_plugins = {}  # type: dict[str, type]
    load_plugins(SanityFunc, sanity_plugins)
    sanity_tests = tuple([plugin() for plugin in sanity_plugins.values()])
    global SANITY_TESTS  # pylint: disable=locally-disabled, global-statement
    SANITY_TESTS = tuple(sorted(sanity_tests + collect_code_smell_tests(), key=lambda k: k.name))
