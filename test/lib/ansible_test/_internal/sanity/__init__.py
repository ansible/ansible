"""Execute Ansible sanity tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import glob
import json
import os
import re
import collections

from .. import types as t

from ..util import (
    ApplicationError,
    SubprocessError,
    display,
    import_plugins,
    load_plugins,
    parse_to_list_of_dict,
    ABC,
    ANSIBLE_TEST_DATA_ROOT,
    is_binary_file,
    read_lines_without_comments,
    get_available_python_versions,
    find_python,
    is_subdir,
    paths_to_dirs,
    get_ansible_version,
)

from ..util_common import (
    run_command,
    handle_layout_messages,
)

from ..ansible_util import (
    ansible_environment,
    check_pyyaml,
)

from ..target import (
    walk_internal_targets,
    walk_sanity_targets,
    TestTarget,
)

from ..executor import (
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
    install_command_requirements,
    SUPPORTED_PYTHON_VERSIONS,
)

from ..config import (
    SanityConfig,
)

from ..test import (
    TestSuccess,
    TestFailure,
    TestSkipped,
    TestMessage,
    calculate_best_confidence,
)

from ..data import (
    data_context,
)

COMMAND = 'sanity'
SANITY_ROOT = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'sanity')


def command_sanity(args):
    """
    :type args: SanityConfig
    """
    handle_layout_messages(data_context().content.sanity_messages)

    changes = get_changes_filter(args)
    require = args.require + changes
    targets = SanityTargets.create(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes, exclude=args.exclude)

    tests = sanity_get_tests()

    if args.test:
        tests = [target for target in tests if target.name in args.test]
    else:
        disabled = [target.name for target in tests if not target.enabled and not args.allow_disabled]
        tests = [target for target in tests if target.enabled or args.allow_disabled]

        if disabled:
            display.warning('Skipping tests disabled by default without --allow-disabled: %s' % ', '.join(sorted(disabled)))

    if args.skip_test:
        tests = [target for target in tests if target.name not in args.skip_test]

    total = 0
    failed = []

    requirements_installed = set()  # type: t.Set[str]

    for test in tests:
        if args.list_tests:
            display.info(test.name)
            continue

        available_versions = sorted(get_available_python_versions(SUPPORTED_PYTHON_VERSIONS).keys())

        if args.python:
            # specific version selected
            versions = (args.python,)
        elif isinstance(test, SanityMultipleVersion):
            # try all supported versions for multi-version tests when a specific version has not been selected
            versions = test.supported_python_versions
        elif not test.supported_python_versions or args.python_version in test.supported_python_versions:
            # the test works with any version or the version we're already running
            versions = (args.python_version,)
        else:
            # available versions supported by the test
            versions = tuple(sorted(set(available_versions) & set(test.supported_python_versions)))
            # use the lowest available version supported by the test or the current version as a fallback (which will be skipped)
            versions = versions[:1] or (args.python_version,)

        for version in versions:
            if isinstance(test, SanityMultipleVersion):
                skip_version = version
            else:
                skip_version = None

            options = ''

            if test.supported_python_versions and version not in test.supported_python_versions:
                display.warning("Skipping sanity test '%s' on unsupported Python %s." % (test.name, version))
                result = SanitySkipped(test.name, skip_version)
            elif not args.python and version not in available_versions:
                display.warning("Skipping sanity test '%s' on Python %s due to missing interpreter." % (test.name, version))
                result = SanitySkipped(test.name, skip_version)
            else:
                check_pyyaml(args, version)

                if test.supported_python_versions:
                    display.info("Running sanity test '%s' with Python %s" % (test.name, version))
                else:
                    display.info("Running sanity test '%s'" % test.name)

                if isinstance(test, SanityCodeSmellTest):
                    settings = test.load_processor(args)
                elif isinstance(test, SanityMultipleVersion):
                    settings = test.load_processor(args, version)
                elif isinstance(test, SanitySingleVersion):
                    settings = test.load_processor(args)
                elif isinstance(test, SanityVersionNeutral):
                    settings = test.load_processor(args)
                else:
                    raise Exception('Unsupported test type: %s' % type(test))

                all_targets = targets.targets

                if test.all_targets:
                    usable_targets = targets.targets
                elif test.no_targets:
                    usable_targets = tuple()
                else:
                    usable_targets = targets.include

                all_targets = SanityTargets.filter_and_inject_targets(test, all_targets)
                usable_targets = SanityTargets.filter_and_inject_targets(test, usable_targets)

                usable_targets = sorted(test.filter_targets(list(usable_targets)))
                usable_targets = settings.filter_skipped_targets(usable_targets)
                sanity_targets = SanityTargets(tuple(all_targets), tuple(usable_targets))

                if usable_targets or test.no_targets:
                    if version not in requirements_installed:
                        requirements_installed.add(version)
                        install_command_requirements(args, version)

                    if isinstance(test, SanityCodeSmellTest):
                        result = test.test(args, sanity_targets, version)
                    elif isinstance(test, SanityMultipleVersion):
                        result = test.test(args, sanity_targets, version)
                        options = ' --python %s' % version
                    elif isinstance(test, SanitySingleVersion):
                        result = test.test(args, sanity_targets, version)
                    elif isinstance(test, SanityVersionNeutral):
                        result = test.test(args, sanity_targets)
                    else:
                        raise Exception('Unsupported test type: %s' % type(test))
                else:
                    result = SanitySkipped(test.name, skip_version)

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


def collect_code_smell_tests():  # type: () -> t.Tuple[SanityFunc, ...]
    """Return a tuple of available code smell sanity tests."""
    paths = glob.glob(os.path.join(SANITY_ROOT, 'code-smell', '*.py'))

    if data_context().content.is_ansible:
        # include Ansible specific code-smell tests which are not configured to be skipped
        ansible_code_smell_root = os.path.join(data_context().content.root, 'test', 'sanity', 'code-smell')
        skip_tests = read_lines_without_comments(os.path.join(ansible_code_smell_root, 'skip.txt'), remove_blank_lines=True, optional=True)
        paths.extend(path for path in glob.glob(os.path.join(ansible_code_smell_root, '*.py')) if os.path.basename(path) not in skip_tests)

    paths = sorted(p for p in paths if os.access(p, os.X_OK) and os.path.isfile(p))
    tests = tuple(SanityCodeSmellTest(p) for p in paths)

    return tests


def sanity_get_tests():
    """
    :rtype: tuple[SanityFunc]
    """
    return SANITY_TESTS


class SanityIgnoreParser:
    """Parser for the consolidated sanity test ignore file."""
    NO_CODE = '_'

    def __init__(self, args):  # type: (SanityConfig) -> None
        if data_context().content.collection:
            ansible_version = '%s.%s' % tuple(get_ansible_version().split('.')[:2])

            ansible_label = 'Ansible %s' % ansible_version
            file_name = 'ignore-%s.txt' % ansible_version
        else:
            ansible_label = 'Ansible'
            file_name = 'ignore.txt'

        self.args = args
        self.relative_path = os.path.join(data_context().content.sanity_path, file_name)
        self.path = os.path.join(data_context().content.root, self.relative_path)
        self.ignores = collections.defaultdict(lambda: collections.defaultdict(dict))  # type: t.Dict[str, t.Dict[str, t.Dict[str, int]]]
        self.skips = collections.defaultdict(lambda: collections.defaultdict(int))  # type: t.Dict[str, t.Dict[str, int]]
        self.parse_errors = []  # type: t.List[t.Tuple[int, int, str]]
        self.file_not_found_errors = []  # type: t.List[t.Tuple[int, str]]

        lines = read_lines_without_comments(self.path, optional=True)
        targets = SanityTargets.get_targets()
        paths = set(target.path for target in targets)
        tests_by_name = {}  # type: t.Dict[str, SanityTest]
        versioned_test_names = set()  # type: t.Set[str]
        unversioned_test_names = {}  # type: t.Dict[str, str]
        directories = paths_to_dirs(list(paths))
        paths_by_test = {}  # type: t.Dict[str, t.Set[str]]

        display.info('Read %d sanity test ignore line(s) for %s from: %s' % (len(lines), ansible_label, self.relative_path), verbosity=1)

        for test in sanity_get_tests():
            test_targets = SanityTargets.filter_and_inject_targets(test, targets)

            paths_by_test[test.name] = set(target.path for target in test.filter_targets(test_targets))

            if isinstance(test, SanityMultipleVersion):
                versioned_test_names.add(test.name)
                tests_by_name.update(dict(('%s-%s' % (test.name, python_version), test) for python_version in test.supported_python_versions))
            else:
                unversioned_test_names.update(dict(('%s-%s' % (test.name, python_version), test.name) for python_version in SUPPORTED_PYTHON_VERSIONS))
                tests_by_name[test.name] = test

        for line_no, line in enumerate(lines, start=1):
            if not line:
                self.parse_errors.append((line_no, 1, "Line cannot be empty or contain only a comment"))
                continue

            parts = line.split(' ')
            path = parts[0]
            codes = parts[1:]

            if not path:
                self.parse_errors.append((line_no, 1, "Line cannot start with a space"))
                continue

            if path.endswith(os.path.sep):
                if path not in directories:
                    self.file_not_found_errors.append((line_no, path))
                    continue
            else:
                if path not in paths:
                    self.file_not_found_errors.append((line_no, path))
                    continue

            if not codes:
                self.parse_errors.append((line_no, len(path), "Error code required after path"))
                continue

            code = codes[0]

            if not code:
                self.parse_errors.append((line_no, len(path) + 1, "Error code after path cannot be empty"))
                continue

            if len(codes) > 1:
                self.parse_errors.append((line_no, len(path) + len(code) + 2, "Error code cannot contain spaces"))
                continue

            parts = code.split('!')
            code = parts[0]
            commands = parts[1:]

            parts = code.split(':')
            test_name = parts[0]
            error_codes = parts[1:]

            test = tests_by_name.get(test_name)

            if not test:
                unversioned_name = unversioned_test_names.get(test_name)

                if unversioned_name:
                    self.parse_errors.append((line_no, len(path) + len(unversioned_name) + 2, "Sanity test '%s' cannot use a Python version like '%s'" % (
                        unversioned_name, test_name)))
                elif test_name in versioned_test_names:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + 1, "Sanity test '%s' requires a Python version like '%s-%s'" % (
                        test_name, test_name, args.python_version)))
                else:
                    self.parse_errors.append((line_no, len(path) + 2, "Sanity test '%s' does not exist" % test_name))

                continue

            if path.endswith(os.path.sep) and not test.include_directories:
                self.parse_errors.append((line_no, 1, "Sanity test '%s' does not support directory paths" % test_name))
                continue

            if path not in paths_by_test[test.name] and not test.no_targets:
                self.parse_errors.append((line_no, 1, "Sanity test '%s' does not test path '%s'" % (test_name, path)))
                continue

            if commands and error_codes:
                self.parse_errors.append((line_no, len(path) + len(test_name) + 2, "Error code cannot contain both '!' and ':' characters"))
                continue

            if commands:
                command = commands[0]

                if len(commands) > 1:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + len(command) + 3, "Error code cannot contain multiple '!' characters"))
                    continue

                if command == 'skip':
                    if not test.can_skip:
                        self.parse_errors.append((line_no, len(path) + len(test_name) + 2, "Sanity test '%s' cannot be skipped" % test_name))
                        continue

                    existing_line_no = self.skips.get(test_name, {}).get(path)

                    if existing_line_no:
                        self.parse_errors.append((line_no, 1, "Duplicate '%s' skip for path '%s' first found on line %d" % (test_name, path, existing_line_no)))
                        continue

                    self.skips[test_name][path] = line_no
                    continue

                self.parse_errors.append((line_no, len(path) + len(test_name) + 2, "Command '!%s' not recognized" % command))
                continue

            if not test.can_ignore:
                self.parse_errors.append((line_no, len(path) + 1, "Sanity test '%s' cannot be ignored" % test_name))
                continue

            if test.error_code:
                if not error_codes:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + 1, "Sanity test '%s' requires an error code" % test_name))
                    continue

                error_code = error_codes[0]

                if len(error_codes) > 1:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + len(error_code) + 3, "Error code cannot contain multiple ':' characters"))
                    continue
            else:
                if error_codes:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + 2, "Sanity test '%s' does not support error codes" % test_name))
                    continue

                error_code = self.NO_CODE

            existing = self.ignores.get(test_name, {}).get(path, {}).get(error_code)

            if existing:
                if test.error_code:
                    self.parse_errors.append((line_no, 1, "Duplicate '%s' ignore for error code '%s' for path '%s' first found on line %d" % (
                        test_name, error_code, path, existing)))
                else:
                    self.parse_errors.append((line_no, 1, "Duplicate '%s' ignore for path '%s' first found on line %d" % (
                        test_name, path, existing)))

                continue

            self.ignores[test_name][path][error_code] = line_no

    @staticmethod
    def load(args):  # type: (SanityConfig) -> SanityIgnoreParser
        """Return the current SanityIgnore instance, initializing it if needed."""
        try:
            return SanityIgnoreParser.instance
        except AttributeError:
            pass

        SanityIgnoreParser.instance = SanityIgnoreParser(args)
        return SanityIgnoreParser.instance


class SanityIgnoreProcessor:
    """Processor for sanity test ignores for a single run of one sanity test."""
    def __init__(self,
                 args,  # type: SanityConfig
                 test,  # type: SanityTest
                 python_version,  # type: t.Optional[str]
                 ):  # type: (...) -> None
        name = test.name
        code = test.error_code

        if python_version:
            full_name = '%s-%s' % (name, python_version)
        else:
            full_name = name

        self.args = args
        self.test = test
        self.code = code
        self.parser = SanityIgnoreParser.load(args)
        self.ignore_entries = self.parser.ignores.get(full_name, {})
        self.skip_entries = self.parser.skips.get(full_name, {})
        self.used_line_numbers = set()  # type: t.Set[int]

    def filter_skipped_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given targets, with any skipped paths filtered out."""
        return sorted(target for target in targets if target.path not in self.skip_entries)

    def process_errors(self, errors, paths):  # type: (t.List[SanityMessage], t.List[str]) -> t.List[SanityMessage]
        """Return the given errors filtered for ignores and with any settings related errors included."""
        errors = self.filter_messages(errors)
        errors.extend(self.get_errors(paths))

        errors = sorted(set(errors))

        return errors

    def filter_messages(self, messages):  # type: (t.List[SanityMessage]) -> t.List[SanityMessage]
        """Return a filtered list of the given messages using the entries that have been loaded."""
        filtered = []

        for message in messages:
            path_entry = self.ignore_entries.get(message.path)

            if path_entry:
                code = message.code if self.code else SanityIgnoreParser.NO_CODE
                line_no = path_entry.get(code)

                if line_no:
                    self.used_line_numbers.add(line_no)
                    continue

            filtered.append(message)

        return filtered

    def get_errors(self, paths):  # type: (t.List[str]) -> t.List[SanityMessage]
        """Return error messages related to issues with the file."""
        messages = []

        # unused errors

        unused = []  # type: t.List[t.Tuple[int, str, str]]

        if self.test.no_targets or self.test.all_targets:
            # tests which do not accept a target list, or which use all targets, always return all possible errors, so all ignores can be checked
            targets = SanityTargets.get_targets()
            test_targets = SanityTargets.filter_and_inject_targets(self.test, targets)
            paths = [target.path for target in test_targets]

        for path in paths:
            path_entry = self.ignore_entries.get(path)

            if not path_entry:
                continue

            unused.extend((line_no, path, code) for code, line_no in path_entry.items() if line_no not in self.used_line_numbers)

        messages.extend(SanityMessage(
            code=self.code,
            message="Ignoring '%s' on '%s' is unnecessary" % (code, path) if self.code else "Ignoring '%s' is unnecessary" % path,
            path=self.parser.relative_path,
            line=line,
            column=1,
            confidence=calculate_best_confidence(((self.parser.path, line), (path, 0)), self.args.metadata) if self.args.metadata.changes else None,
        ) for line, path, code in unused)

        return messages


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


class SanityTargets:
    """Sanity test target information."""
    def __init__(self, targets, include):  # type: (t.Tuple[TestTarget], t.Tuple[TestTarget]) -> None
        self.targets = targets
        self.include = include

    @staticmethod
    def create(include, exclude, require):  # type: (t.List[str], t.List[str], t.List[str]) -> SanityTargets
        """Create a SanityTargets instance from the given include, exclude and require lists."""
        _targets = SanityTargets.get_targets()
        _include = walk_internal_targets(_targets, include, exclude, require)
        return SanityTargets(_targets, _include)

    @staticmethod
    def filter_and_inject_targets(test, targets):  # type: (SanityTest, t.Iterable[TestTarget]) -> t.List[TestTarget]
        """Filter and inject targets based on test requirements and the given target list."""
        test_targets = list(targets)

        if not test.include_symlinks:
            # remove all symlinks unless supported by the test
            test_targets = [target for target in test_targets if not target.symlink]

        if not test.include_directories or not test.include_symlinks:
            # exclude symlinked directories unless supported by the test
            test_targets = [target for target in test_targets if not target.path.endswith(os.path.sep)]

        if test.include_directories:
            # include directories containing any of the included files
            test_targets += tuple(TestTarget(path, None, None, '') for path in paths_to_dirs([target.path for target in test_targets]))

            if not test.include_symlinks:
                # remove all directory symlinks unless supported by the test
                test_targets = [target for target in test_targets if not target.symlink]

        return test_targets

    @staticmethod
    def get_targets():  # type: () -> t.Tuple[TestTarget, ...]
        """Return a tuple of sanity test targets. Uses a cached version when available."""
        try:
            return SanityTargets.get_targets.targets
        except AttributeError:
            SanityTargets.get_targets.targets = tuple(sorted(walk_sanity_targets()))

        return SanityTargets.get_targets.targets


class SanityTest(ABC):
    """Sanity test base class."""
    __metaclass__ = abc.ABCMeta

    ansible_only = False

    def __init__(self, name):
        self.name = name
        self.enabled = True

    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return None

    @property
    def can_ignore(self):  # type: () -> bool
        """True if the test supports ignore entries."""
        return True

    @property
    def can_skip(self):  # type: () -> bool
        """True if the test supports skip entries."""
        return not self.all_targets and not self.no_targets

    @property
    def all_targets(self):  # type: () -> bool
        """True if test targets will not be filtered using includes, excludes, requires or changes. Mutually exclusive with no_targets."""
        return False

    @property
    def no_targets(self):  # type: () -> bool
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return False

    @property
    def include_directories(self):  # type: () -> bool
        """True if the test targets should include directories."""
        return False

    @property
    def include_symlinks(self):  # type: () -> bool
        """True if the test targets should include symlinks."""
        return False

    @property
    def supported_python_versions(self):  # type: () -> t.Optional[t.Tuple[str, ...]]
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return tuple(python_version for python_version in SUPPORTED_PYTHON_VERSIONS if python_version.startswith('3.'))

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        if self.no_targets:
            return []

        raise NotImplementedError('Sanity test "%s" must implement "filter_targets" or set "no_targets" to True.' % self.name)


class SanityCodeSmellTest(SanityTest):
    """Sanity test script."""
    def __init__(self, path):
        name = os.path.splitext(os.path.basename(path))[0]
        config_path = os.path.splitext(path)[0] + '.json'

        super(SanityCodeSmellTest, self).__init__(name)

        self.path = path
        self.config_path = config_path if os.path.exists(config_path) else None
        self.config = None

        if self.config_path:
            with open(self.config_path, 'r') as config_fd:
                self.config = json.load(config_fd)

        if self.config:
            self.enabled = not self.config.get('disabled')

            self.output = self.config.get('output')  # type: t.Optional[str]
            self.extensions = self.config.get('extensions')  # type: t.List[str]
            self.prefixes = self.config.get('prefixes')  # type: t.List[str]
            self.files = self.config.get('files')  # type: t.List[str]
            self.text = self.config.get('text')  # type: t.Optional[bool]
            self.ignore_self = self.config.get('ignore_self')  # type: bool

            self.__all_targets = self.config.get('all_targets')  # type: bool
            self.__no_targets = self.config.get('no_targets')  # type: bool
            self.__include_directories = self.config.get('include_directories')  # type: bool
            self.__include_symlinks = self.config.get('include_symlinks')  # type: bool
        else:
            self.output = None
            self.extensions = []
            self.prefixes = []
            self.files = []
            self.text = None  # type: t.Optional[bool]
            self.ignore_self = False

            self.__all_targets = False
            self.__no_targets = True
            self.__include_directories = False
            self.__include_symlinks = False

        if self.no_targets:
            mutually_exclusive = (
                'extensions',
                'prefixes',
                'files',
                'text',
                'ignore_self',
                'all_targets',
                'include_directories',
                'include_symlinks',
            )

            problems = sorted(name for name in mutually_exclusive if getattr(self, name))

            if problems:
                raise ApplicationError('Sanity test "%s" option "no_targets" is mutually exclusive with options: %s' % (self.name, ', '.join(problems)))

    @property
    def all_targets(self):  # type: () -> bool
        """True if test targets will not be filtered using includes, excludes, requires or changes. Mutually exclusive with no_targets."""
        return self.__all_targets

    @property
    def no_targets(self):  # type: () -> bool
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return self.__no_targets

    @property
    def include_directories(self):  # type: () -> bool
        """True if the test targets should include directories."""
        return self.__include_directories

    @property
    def include_symlinks(self):  # type: () -> bool
        """True if the test targets should include symlinks."""
        return self.__include_symlinks

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        if self.no_targets:
            return []

        if self.text is not None:
            if self.text:
                targets = [target for target in targets if not is_binary_file(target.path)]
            else:
                targets = [target for target in targets if is_binary_file(target.path)]

        if self.extensions:
            targets = [target for target in targets if os.path.splitext(target.path)[1] in self.extensions
                       or (is_subdir(target.path, 'bin') and '.py' in self.extensions)]

        if self.prefixes:
            targets = [target for target in targets if any(target.path.startswith(pre) for pre in self.prefixes)]

        if self.files:
            targets = [target for target in targets if os.path.basename(target.path) in self.files]

        if self.ignore_self and data_context().content.is_ansible:
            relative_self_path = os.path.relpath(self.path, data_context().content.root)
            targets = [target for target in targets if target.path != relative_self_path]

        return targets

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        cmd = [find_python(python_version), self.path]

        env = ansible_environment(args, color=False)

        pattern = None
        data = None

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        if self.config:
            if self.output == 'path-line-column-message':
                pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'
            elif self.output == 'path-message':
                pattern = '^(?P<path>[^:]*): (?P<message>.*)$'
            else:
                pattern = ApplicationError('Unsupported output type: %s' % self.output)

        if not self.no_targets:
            data = '\n'.join(paths)

            if data:
                display.info(data, verbosity=4)

        try:
            stdout, stderr = run_command(args, cmd, data=data, env=env, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if args.explain:
            return SanitySuccess(self.name)

        if stdout and not stderr:
            if pattern:
                matches = parse_to_list_of_dict(pattern, stdout)

                messages = [SanityMessage(
                    message=m['message'],
                    path=m['path'],
                    line=int(m.get('line', 0)),
                    column=int(m.get('column', 0)),
                ) for m in matches]

                messages = settings.process_errors(messages, paths)

                if not messages:
                    return SanitySuccess(self.name)

                return SanityFailure(self.name, messages=messages)

        if stderr or status:
            summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
            return SanityFailure(self.name, summary=summary)

        messages = settings.process_errors([], paths)

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)

    def load_processor(self, args):  # type: (SanityConfig) -> SanityIgnoreProcessor
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)


class SanityFunc(SanityTest):
    """Base class for sanity test plugins."""
    def __init__(self):
        name = self.__class__.__name__
        name = re.sub(r'Test$', '', name)  # drop Test suffix
        name = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', name).lower()  # use dashes instead of capitalization

        super(SanityFunc, self).__init__(name)


class SanityVersionNeutral(SanityFunc):
    """Base class for sanity test plugins which are idependent of the python version being used."""
    @abc.abstractmethod
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """

    def load_processor(self, args):  # type: (SanityConfig) -> SanityIgnoreProcessor
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)

    @property
    def supported_python_versions(self):  # type: () -> t.Optional[t.Tuple[str, ...]]
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return None


class SanitySingleVersion(SanityFunc):
    """Base class for sanity test plugins which should run on a single python version."""
    @abc.abstractmethod
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """

    def load_processor(self, args):  # type: (SanityConfig) -> SanityIgnoreProcessor
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)


class SanityMultipleVersion(SanityFunc):
    """Base class for sanity test plugins which should run on multiple python versions."""
    @abc.abstractmethod
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """

    def load_processor(self, args, python_version):  # type: (SanityConfig, str) -> SanityIgnoreProcessor
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, python_version)

    @property
    def supported_python_versions(self):  # type: () -> t.Optional[t.Tuple[str, ...]]
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return SUPPORTED_PYTHON_VERSIONS


SANITY_TESTS = (
)


def sanity_init():
    """Initialize full sanity test list (includes code-smell scripts determined at runtime)."""
    import_plugins('sanity')
    sanity_plugins = {}  # type: t.Dict[str, t.Type[SanityFunc]]
    load_plugins(SanityFunc, sanity_plugins)
    sanity_tests = tuple([plugin() for plugin in sanity_plugins.values() if data_context().content.is_ansible or not plugin.ansible_only])
    global SANITY_TESTS  # pylint: disable=locally-disabled, global-statement
    SANITY_TESTS = tuple(sorted(sanity_tests + collect_code_smell_tests(), key=lambda k: k.name))
