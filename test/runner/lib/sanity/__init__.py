"""Execute Ansible sanity tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import glob
import json
import os
import re
import collections

import lib.types as t

from lib.util import (
    ApplicationError,
    SubprocessError,
    display,
    import_plugins,
    load_plugins,
    parse_to_list_of_dict,
    ABC,
    ANSIBLE_ROOT,
    is_binary_file,
    read_lines_without_comments,
)

from lib.util_common import (
    run_command,
)

from lib.ansible_util import (
    ansible_environment,
    check_pyyaml,
)

from lib.target import (
    walk_internal_targets,
    walk_sanity_targets,
    TestTarget,
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
    calculate_best_confidence,
    calculate_confidence,
)

from lib.data import (
    data_context,
)

COMMAND = 'sanity'


def command_sanity(args):
    """
    :type args: SanityConfig
    """
    changes = get_changes_filter(args)
    require = args.require + changes
    targets = SanityTargets(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes, exclude=args.exclude)

    install_command_requirements(args)

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

            check_pyyaml(args, version or args.python_version)

            display.info('Sanity check using %s%s' % (test.name, ' with Python %s' % version if version else ''))

            options = ''

            if isinstance(test, SanityCodeSmellTest):
                result = test.test(args, targets)
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
    :rtype: tuple[SanityFunc]
    """
    skip_file = os.path.join(ANSIBLE_ROOT, 'test/sanity/code-smell/skip.txt')
    ansible_only_file = os.path.join(ANSIBLE_ROOT, 'test/sanity/code-smell/ansible-only.txt')

    skip_tests = read_lines_without_comments(skip_file, remove_blank_lines=True, optional=True)

    if not data_context().content.is_ansible:
        skip_tests += read_lines_without_comments(ansible_only_file, remove_blank_lines=True)

    paths = glob.glob(os.path.join(ANSIBLE_ROOT, 'test/sanity/code-smell/*'))
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


class SanityTargets:
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


class SanityTest(ABC):
    """Sanity test base class."""
    __metaclass__ = abc.ABCMeta

    ansible_only = False

    def __init__(self, name):
        self.name = name
        self.enabled = True


class SanityCodeSmellTest(SanityTest):
    """Sanity test script."""
    UNSUPPORTED_PYTHON_VERSIONS = (
        '2.6',  # some tests use voluptuous, but the version we require does not support python 2.6
    )

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

    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        if args.python_version in self.UNSUPPORTED_PYTHON_VERSIONS:
            display.warning('Skipping %s on unsupported Python version %s.' % (self.name, args.python_version))
            return SanitySkipped(self.name)

        if self.path.endswith('.py'):
            cmd = [args.python_executable, self.path]
        else:
            cmd = [self.path]

        env = ansible_environment(args, color=False)

        pattern = None
        data = None

        if self.config:
            output = self.config.get('output')
            extensions = self.config.get('extensions')
            prefixes = self.config.get('prefixes')
            files = self.config.get('files')
            always = self.config.get('always')
            text = self.config.get('text')
            ignore_changes = self.config.get('ignore_changes')

            if output == 'path-line-column-message':
                pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'
            elif output == 'path-message':
                pattern = '^(?P<path>[^:]*): (?P<message>.*)$'
            else:
                pattern = ApplicationError('Unsupported output type: %s' % output)

            if ignore_changes:
                paths = sorted(i.path for i in targets.targets)
                always = False
            else:
                paths = sorted(i.path for i in targets.include)

            if always:
                paths = []

            if text is not None:
                if text:
                    paths = [p for p in paths if not is_binary_file(p)]
                else:
                    paths = [p for p in paths if is_binary_file(p)]

            if extensions:
                paths = [p for p in paths if os.path.splitext(p)[1] in extensions or (p.startswith('bin/') and '.py' in extensions)]

            if prefixes:
                paths = [p for p in paths if any(p.startswith(pre) for pre in prefixes)]

            if files:
                paths = [p for p in paths if os.path.basename(p) in files]

            if not paths and not always:
                return SanitySkipped(self.name)

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

        if stdout and not stderr:
            if pattern:
                matches = parse_to_list_of_dict(pattern, stdout)

                messages = [SanityMessage(
                    message=m['message'],
                    path=m['path'],
                    line=int(m.get('line', 0)),
                    column=int(m.get('column', 0)),
                ) for m in matches]

                return SanityFailure(self.name, messages=messages)

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
        :rtype: TestResult
        """

    def load_settings(self, args, code):  # type: (SanityConfig, t.Optional[str]) -> SanitySettings
        """Load settings for this sanity test."""
        return SanitySettings(args, self.name, code, None)


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

    def load_settings(self, args, code, python_version):  # type: (SanityConfig, t.Optional[str], t.Optional[str]) -> SanitySettings
        """Load settings for this sanity test."""
        return SanitySettings(args, self.name, code, python_version)


class SanitySettings:
    """Settings for sanity tests."""
    def __init__(self,
                 args,  # type: SanityConfig
                 name,  # type: str
                 code,  # type: t.Optional[str]
                 python_version,  # type: t.Optional[str]
                 ):  # type: (...) -> None
        self.args = args
        self.code = code
        self.ignore_settings = SanitySettingsFile(args, name, 'ignore', code, python_version)
        self.skip_settings = SanitySettingsFile(args, name, 'skip', code, python_version)

    def filter_skipped_paths(self, paths):  # type: (t.List[str]) -> t.List[str]
        """Return the given paths, with any skipped paths filtered out."""
        return sorted(set(paths) - set(self.skip_settings.entries.keys()))

    def filter_skipped_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given targets, with any skipped paths filtered out."""
        return sorted(target for target in targets if target.path not in self.skip_settings.entries)

    def process_errors(self, errors, paths):  # type: (t.List[SanityMessage], t.List[str]) -> t.List[SanityMessage]
        """Return the given errors filtered for ignores and with any settings related errors included."""
        errors = self.ignore_settings.filter_messages(errors)
        errors.extend(self.ignore_settings.get_errors(paths))
        errors.extend(self.skip_settings.get_errors([]))

        for ignore_path, ignore_entry in self.ignore_settings.entries.items():
            skip_entry = self.skip_settings.entries.get(ignore_path)

            if not skip_entry:
                continue

            skip_line_no = skip_entry[SanitySettingsFile.NO_CODE]

            for ignore_line_no in ignore_entry.values():
                candidates = ((self.ignore_settings.path, ignore_line_no), (self.skip_settings.path, skip_line_no))

                errors.append(SanityMessage(
                    code=self.code,
                    message="Ignoring '%s' is unnecessary due to skip entry on line %d of '%s'" % (ignore_path, skip_line_no, self.skip_settings.relative_path),
                    path=self.ignore_settings.relative_path,
                    line=ignore_line_no,
                    column=1,
                    confidence=calculate_best_confidence(candidates, self.args.metadata) if self.args.metadata.changes else None,
                ))

        errors = sorted(set(errors))

        return errors


class SanitySettingsFile:
    """Interface to sanity ignore or sanity skip file settings."""
    NO_CODE = '_'

    def __init__(self,
                 args,  # type: SanityConfig
                 name,  # type: str
                 mode,  # type: str
                 code,  # type: t.Optional[str]
                 python_version,  # type: t.Optional[str]
                 ):  # type: (...) -> None
        """
        :param mode: must be either "ignore" or "skip"
        :param code: a code for ansible-test to use for internal errors, using a style that matches codes used by the test, or None if codes are not used
        """
        if mode == 'ignore':
            self.parse_codes = bool(code)
        elif mode == 'skip':
            self.parse_codes = False
        else:
            raise Exception('Unsupported mode: %s' % mode)

        if name == 'compile':
            filename = 'python%s-%s' % (python_version, mode)
        else:
            filename = '%s-%s' % (mode, python_version) if python_version else mode

        self.args = args
        self.code = code
        self.relative_path = 'test/sanity/%s/%s.txt' % (name, filename)
        self.path = os.path.join(data_context().content.root, self.relative_path)
        self.entries = collections.defaultdict(dict)  # type: t.Dict[str, t.Dict[str, int]]
        self.parse_errors = []  # type: t.List[t.Tuple[int, int, str]]
        self.file_not_found_errors = []  # type: t.List[t.Tuple[int, str]]
        self.used_line_numbers = set()  # type: t.Set[int]

        lines = read_lines_without_comments(self.path, optional=True)
        paths = set(data_context().content.all_files())

        for line_no, line in enumerate(lines, start=1):
            if not line:
                continue

            if line.startswith(' '):
                self.parse_errors.append((line_no, 1, 'Line cannot start with a space'))
                continue

            if line.endswith(' '):
                self.parse_errors.append((line_no, len(line), 'Line cannot end with a space'))
                continue

            parts = line.split(' ')
            path = parts[0]

            if path not in paths:
                self.file_not_found_errors.append((line_no, path))
                continue

            if self.parse_codes:
                if len(parts) < 2:
                    self.parse_errors.append((line_no, len(line), 'Code required after path'))
                    continue

                code = parts[1]

                if not code:
                    self.parse_errors.append((line_no, len(path) + 1, 'Code after path cannot be empty'))
                    continue

                if len(parts) > 2:
                    self.parse_errors.append((line_no, len(path) + len(code) + 2, 'Code cannot contain spaces'))
                    continue

                existing = self.entries.get(path, {}).get(code)

                if existing:
                    self.parse_errors.append((line_no, 1, "Duplicate code '%s' for path '%s' first found on line %d" % (code, path, existing)))
                    continue
            else:
                if len(parts) > 1:
                    self.parse_errors.append((line_no, len(path) + 1, 'Path cannot contain spaces'))
                    continue

                code = self.NO_CODE
                existing = self.entries.get(path)

                if existing:
                    self.parse_errors.append((line_no, 1, "Duplicate path '%s' first found on line %d" % (path, existing[code])))
                    continue

            self.entries[path][code] = line_no

    def filter_messages(self, messages):  # type: (t.List[SanityMessage]) -> t.List[SanityMessage]
        """Return a filtered list of the given messages using the entries that have been loaded."""
        filtered = []

        for message in messages:
            path_entry = self.entries.get(message.path)

            if path_entry:
                code = message.code if self.code else self.NO_CODE
                line_no = path_entry.get(code)

                if line_no:
                    self.used_line_numbers.add(line_no)
                    continue

            filtered.append(message)

        return filtered

    def get_errors(self, paths):  # type: (t.List[str]) -> t.List[SanityMessage]
        """Return error messages related to issues with the file."""
        messages = []

        # parse errors

        messages.extend(SanityMessage(
            code=self.code,
            message=message,
            path=self.relative_path,
            line=line,
            column=column,
            confidence=calculate_confidence(self.path, line, self.args.metadata) if self.args.metadata.changes else None,
        ) for line, column, message in self.parse_errors)

        # file not found errors

        messages.extend(SanityMessage(
            code=self.code,
            message="File '%s' does not exist" % path,
            path=self.relative_path,
            line=line,
            column=1,
            confidence=calculate_best_confidence(((self.path, line), (path, 0)), self.args.metadata) if self.args.metadata.changes else None,
        ) for line, path in self.file_not_found_errors)

        # unused errors

        unused = []  # type: t.List[t.Tuple[int, str, str]]

        for path in paths:
            path_entry = self.entries.get(path)

            if not path_entry:
                continue

            unused.extend((line_no, path, code) for code, line_no in path_entry.items() if line_no not in self.used_line_numbers)

        messages.extend(SanityMessage(
            code=self.code,
            message="Ignoring '%s' on '%s' is unnecessary" % (code, path) if self.code else "Ignoring '%s' is unnecessary" % path,
            path=self.relative_path,
            line=line,
            column=1,
            confidence=calculate_best_confidence(((self.path, line), (path, 0)), self.args.metadata) if self.args.metadata.changes else None,
        ) for line, path, code in unused)

        return messages


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
