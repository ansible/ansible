"""Execute Ansible sanity tests."""
from __future__ import annotations

import abc
import glob
import hashlib
import json
import os
import pathlib
import re
import collections
import collections.abc as c
import typing as t

from ...constants import (
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_ONLY_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from ...encoding import (
    to_bytes,
)

from ...io import (
    read_json_file,
    write_json_file,
    write_text_file,
)

from ...util import (
    ApplicationError,
    SubprocessError,
    display,
    import_plugins,
    load_plugins,
    parse_to_list_of_dict,
    ANSIBLE_TEST_CONTROLLER_ROOT,
    ANSIBLE_TEST_TARGET_ROOT,
    is_binary_file,
    read_lines_without_comments,
    is_subdir,
    paths_to_dirs,
    get_ansible_version,
    str_to_version,
    cache,
    remove_tree,
)

from ...util_common import (
    intercept_python,
    handle_layout_messages,
    yamlcheck,
    create_result_directories,
)

from ...ansible_util import (
    ansible_environment,
)

from ...target import (
    walk_internal_targets,
    walk_sanity_targets,
    TestTarget,
)

from ...executor import (
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
)

from ...python_requirements import (
    PipCommand,
    PipInstall,
    collect_requirements,
    run_pip,
)

from ...config import (
    SanityConfig,
)

from ...test import (
    TestSuccess,
    TestFailure,
    TestSkipped,
    TestMessage,
    TestResult,
    calculate_best_confidence,
)

from ...data import (
    data_context,
)

from ...content_config import (
    get_content_config,
)

from ...host_configs import (
    DockerConfig,
    PosixConfig,
    PythonConfig,
    VirtualPythonConfig,
)

from ...host_profiles import (
    PosixProfile,
)

from ...provisioning import (
    prepare_profiles,
)

from ...pypi_proxy import (
    configure_pypi_proxy,
)

from ...venv import (
    create_virtual_environment,
)

COMMAND = 'sanity'
SANITY_ROOT = os.path.join(ANSIBLE_TEST_CONTROLLER_ROOT, 'sanity')
TARGET_SANITY_ROOT = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'sanity')

# NOTE: must match ansible.constants.DOCUMENTABLE_PLUGINS, but with 'module' replaced by 'modules'!
DOCUMENTABLE_PLUGINS = (
    'become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory', 'lookup', 'netconf', 'modules', 'shell', 'strategy', 'vars'
)

created_venvs: list[str] = []


def command_sanity(args: SanityConfig) -> None:
    """Run sanity tests."""
    create_result_directories(args)

    target_configs = t.cast(list[PosixConfig], args.targets)
    target_versions: dict[str, PosixConfig] = {target.python.version: target for target in target_configs}

    handle_layout_messages(data_context().content.sanity_messages)

    changes = get_changes_filter(args)
    require = args.require + changes
    targets = SanityTargets.create(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    tests = list(sanity_get_tests())

    if args.test:
        disabled = []
        tests = [target for target in tests if target.name in args.test]
    else:
        disabled = [target.name for target in tests if not target.enabled and not args.allow_disabled]
        tests = [target for target in tests if target.enabled or args.allow_disabled]

    if args.skip_test:
        tests = [target for target in tests if target.name not in args.skip_test]

    if not args.host_path:
        for test in tests:
            test.origin_hook(args)

    targets_use_pypi = any(isinstance(test, SanityMultipleVersion) and test.needs_pypi for test in tests) and not args.list_tests
    host_state = prepare_profiles(args, targets_use_pypi=targets_use_pypi)  # sanity

    get_content_config(args)  # make sure content config has been parsed prior to delegation

    if args.delegate:
        raise Delegate(host_state=host_state, require=changes, exclude=args.exclude)

    configure_pypi_proxy(args, host_state.controller_profile)  # sanity

    if disabled:
        display.warning('Skipping tests disabled by default without --allow-disabled: %s' % ', '.join(sorted(disabled)))

    target_profiles: dict[str, PosixProfile] = {profile.config.python.version: profile for profile in host_state.targets(PosixProfile)}

    total = 0
    failed = []

    result: t.Optional[TestResult]

    for test in tests:
        if args.list_tests:
            print(test.name)  # display goes to stderr, this should be on stdout
            continue

        for version in SUPPORTED_PYTHON_VERSIONS:
            options = ''

            if isinstance(test, SanityMultipleVersion):
                if version not in target_versions and version not in args.host_settings.skipped_python_versions:
                    continue  # version was not requested, skip it silently
            else:
                if version != args.controller_python.version:
                    continue  # only multi-version sanity tests use target versions, the rest use the controller version

            if test.supported_python_versions and version not in test.supported_python_versions:
                result = SanitySkipped(test.name, version)
                result.reason = f'Skipping sanity test "{test.name}" on Python {version} because it is unsupported.' \
                                f' Supported Python versions: {", ".join(test.supported_python_versions)}'
            else:
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

                all_targets = list(targets.targets)

                if test.all_targets:
                    usable_targets = list(targets.targets)
                elif test.no_targets:
                    usable_targets = []
                else:
                    usable_targets = list(targets.include)

                all_targets = SanityTargets.filter_and_inject_targets(test, all_targets)
                usable_targets = SanityTargets.filter_and_inject_targets(test, usable_targets)

                usable_targets = sorted(test.filter_targets_by_version(args, list(usable_targets), version))
                usable_targets = settings.filter_skipped_targets(usable_targets)
                sanity_targets = SanityTargets(tuple(all_targets), tuple(usable_targets))

                test_needed = bool(usable_targets or test.no_targets or args.prime_venvs)
                result = None

                if test_needed and version in args.host_settings.skipped_python_versions:
                    # Deferred checking of Python availability. Done here since it is now known to be required for running the test.
                    # Earlier checking could cause a spurious warning to be generated for a collection which does not support the Python version.
                    # If the user specified a Python version, an error will be generated before reaching this point when the Python interpreter is not found.
                    result = SanitySkipped(test.name, version)
                    result.reason = f'Skipping sanity test "{test.name}" on Python {version} because it could not be found.'

                if not result:
                    if isinstance(test, SanityMultipleVersion):
                        display.info(f'Running sanity test "{test.name}" on Python {version}')
                    else:
                        display.info(f'Running sanity test "{test.name}"')

                if test_needed and not result:
                    if isinstance(test, SanityMultipleVersion):
                        # multi-version sanity tests handle their own requirements (if any) and use the target python
                        test_profile = target_profiles[version]
                        result = test.test(args, sanity_targets, test_profile.python)
                        options = ' --python %s' % version
                    elif isinstance(test, SanitySingleVersion):
                        # single version sanity tests use the controller python
                        test_profile = host_state.controller_profile
                        virtualenv_python = create_sanity_virtualenv(args, test_profile.python, test.name)

                        if virtualenv_python:
                            virtualenv_yaml = check_sanity_virtualenv_yaml(virtualenv_python)

                            if test.require_libyaml and not virtualenv_yaml:
                                result = SanitySkipped(test.name)
                                result.reason = f'Skipping sanity test "{test.name}" on Python {version} due to missing libyaml support in PyYAML.'
                            else:
                                if virtualenv_yaml is False:
                                    display.warning(f'Sanity test "{test.name}" on Python {version} may be slow due to missing libyaml support in PyYAML.')

                                if args.prime_venvs:
                                    result = SanitySkipped(test.name)
                                else:
                                    result = test.test(args, sanity_targets, virtualenv_python)
                        else:
                            result = SanitySkipped(test.name, version)
                            result.reason = f'Skipping sanity test "{test.name}" on Python {version} due to missing virtual environment support.'
                    elif isinstance(test, SanityVersionNeutral):
                        if args.prime_venvs:
                            result = SanitySkipped(test.name)
                        else:
                            # version neutral sanity tests handle their own requirements (if any)
                            result = test.test(args, sanity_targets)
                    else:
                        raise Exception('Unsupported test type: %s' % type(test))
                elif result:
                    pass
                else:
                    result = SanitySkipped(test.name, version)

            result.write(args)

            total += 1

            if isinstance(result, SanityFailure):
                failed.append(result.test + options)

    controller = args.controller

    if created_venvs and isinstance(controller, DockerConfig) and controller.name == 'default' and not args.prime_venvs:
        names = ', '.join(created_venvs)
        display.warning(f'There following sanity test virtual environments are out-of-date in the "default" container: {names}')

    if failed:
        message = 'The %d sanity test(s) listed below (out of %d) failed. See error output above for details.\n%s' % (
            len(failed), total, '\n'.join(failed))

        if args.failure_ok:
            display.error(message)
        else:
            raise ApplicationError(message)


@cache
def collect_code_smell_tests() -> tuple[SanityTest, ...]:
    """Return a tuple of available code smell sanity tests."""
    paths = glob.glob(os.path.join(SANITY_ROOT, 'code-smell', '*.py'))

    if data_context().content.is_ansible:
        # include Ansible specific code-smell tests which are not configured to be skipped
        ansible_code_smell_root = os.path.join(data_context().content.root, 'test', 'sanity', 'code-smell')
        skip_tests = read_lines_without_comments(os.path.join(ansible_code_smell_root, 'skip.txt'), remove_blank_lines=True, optional=True)
        paths.extend(path for path in glob.glob(os.path.join(ansible_code_smell_root, '*.py')) if os.path.basename(path) not in skip_tests)

    tests = tuple(SanityCodeSmellTest(p) for p in paths)

    return tests


class SanityIgnoreParser:
    """Parser for the consolidated sanity test ignore file."""

    NO_CODE = '_'

    def __init__(self, args: SanityConfig) -> None:
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
        self.ignores: dict[str, dict[str, dict[str, int]]] = collections.defaultdict(lambda: collections.defaultdict(dict))
        self.skips: dict[str, dict[str, int]] = collections.defaultdict(lambda: collections.defaultdict(int))
        self.parse_errors: list[tuple[int, int, str]] = []
        self.file_not_found_errors: list[tuple[int, str]] = []

        lines = read_lines_without_comments(self.path, optional=True)
        targets = SanityTargets.get_targets()
        paths = set(target.path for target in targets)
        tests_by_name: dict[str, SanityTest] = {}
        versioned_test_names: set[str] = set()
        unversioned_test_names: dict[str, str] = {}
        directories = paths_to_dirs(list(paths))
        paths_by_test: dict[str, set[str]] = {}

        display.info('Read %d sanity test ignore line(s) for %s from: %s' % (len(lines), ansible_label, self.relative_path), verbosity=1)

        for test in sanity_get_tests():
            test_targets = SanityTargets.filter_and_inject_targets(test, targets)

            if isinstance(test, SanityMultipleVersion):
                versioned_test_names.add(test.name)

                for python_version in test.supported_python_versions:
                    test_name = '%s-%s' % (test.name, python_version)

                    paths_by_test[test_name] = set(target.path for target in test.filter_targets_by_version(args, test_targets, python_version))
                    tests_by_name[test_name] = test
            else:
                unversioned_test_names.update(dict(('%s-%s' % (test.name, python_version), test.name) for python_version in SUPPORTED_PYTHON_VERSIONS))

                paths_by_test[test.name] = set(target.path for target in test.filter_targets_by_version(args, test_targets, ''))
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
                        test_name, test_name, args.controller_python.version)))
                else:
                    self.parse_errors.append((line_no, len(path) + 2, "Sanity test '%s' does not exist" % test_name))

                continue

            if path.endswith(os.path.sep) and not test.include_directories:
                self.parse_errors.append((line_no, 1, "Sanity test '%s' does not support directory paths" % test_name))
                continue

            if path not in paths_by_test[test_name] and not test.no_targets:
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

                if error_code in test.optional_error_codes:
                    self.parse_errors.append((line_no, len(path) + len(test_name) + 3, "Optional error code '%s' cannot be ignored" % (
                        error_code)))
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
    def load(args: SanityConfig) -> SanityIgnoreParser:
        """Return the current SanityIgnore instance, initializing it if needed."""
        try:
            return SanityIgnoreParser.instance  # type: ignore[attr-defined]
        except AttributeError:
            pass

        instance = SanityIgnoreParser(args)

        SanityIgnoreParser.instance = instance  # type: ignore[attr-defined]

        return instance


class SanityIgnoreProcessor:
    """Processor for sanity test ignores for a single run of one sanity test."""

    def __init__(
        self,
        args: SanityConfig,
        test: SanityTest,
        python_version: t.Optional[str],
    ) -> None:
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
        self.used_line_numbers: set[int] = set()

    def filter_skipped_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given targets, with any skipped paths filtered out."""
        return sorted(target for target in targets if target.path not in self.skip_entries)

    def process_errors(self, errors: list[SanityMessage], paths: list[str]) -> list[SanityMessage]:
        """Return the given errors filtered for ignores and with any settings related errors included."""
        errors = self.filter_messages(errors)
        errors.extend(self.get_errors(paths))

        errors = sorted(set(errors))

        return errors

    def filter_messages(self, messages: list[SanityMessage]) -> list[SanityMessage]:
        """Return a filtered list of the given messages using the entries that have been loaded."""
        filtered = []

        for message in messages:
            if message.code in self.test.optional_error_codes and not self.args.enable_optional_errors:
                continue

            path_entry = self.ignore_entries.get(message.path)

            if path_entry:
                code = message.code if self.code else SanityIgnoreParser.NO_CODE
                line_no = path_entry.get(code)

                if line_no:
                    self.used_line_numbers.add(line_no)
                    continue

            filtered.append(message)

        return filtered

    def get_errors(self, paths: list[str]) -> list[SanityMessage]:
        """Return error messages related to issues with the file."""
        messages: list[SanityMessage] = []

        # unused errors

        unused: list[tuple[int, str, str]] = []

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

    def __init__(self, test: str, python_version: t.Optional[str] = None) -> None:
        super().__init__(COMMAND, test, python_version)


class SanitySkipped(TestSkipped):
    """Sanity test skipped."""

    def __init__(self, test: str, python_version: t.Optional[str] = None) -> None:
        super().__init__(COMMAND, test, python_version)


class SanityFailure(TestFailure):
    """Sanity test failure."""

    def __init__(
        self,
        test: str,
        python_version: t.Optional[str] = None,
        messages: t.Optional[c.Sequence[SanityMessage]] = None,
        summary: t.Optional[str] = None,
    ) -> None:
        super().__init__(COMMAND, test, python_version, messages, summary)


class SanityMessage(TestMessage):
    """Single sanity test message for one file."""


class SanityTargets:
    """Sanity test target information."""

    def __init__(self, targets: tuple[TestTarget, ...], include: tuple[TestTarget, ...]) -> None:
        self.targets = targets
        self.include = include

    @staticmethod
    def create(include: list[str], exclude: list[str], require: list[str]) -> SanityTargets:
        """Create a SanityTargets instance from the given include, exclude and require lists."""
        _targets = SanityTargets.get_targets()
        _include = walk_internal_targets(_targets, include, exclude, require)
        return SanityTargets(_targets, _include)

    @staticmethod
    def filter_and_inject_targets(test: SanityTest, targets: c.Iterable[TestTarget]) -> list[TestTarget]:
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
    def get_targets() -> tuple[TestTarget, ...]:
        """Return a tuple of sanity test targets. Uses a cached version when available."""
        try:
            return SanityTargets.get_targets.targets  # type: ignore[attr-defined]
        except AttributeError:
            targets = tuple(sorted(walk_sanity_targets()))

        SanityTargets.get_targets.targets = targets  # type: ignore[attr-defined]

        return targets


class SanityTest(metaclass=abc.ABCMeta):
    """Sanity test base class."""

    ansible_only = False

    def __init__(self, name: t.Optional[str] = None) -> None:
        if not name:
            name = self.__class__.__name__
            name = re.sub(r'Test$', '', name)  # drop Test suffix
            name = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', name).lower()  # use dashes instead of capitalization

        self.name = name
        self.enabled = True

        # Optional error codes represent errors which spontaneously occur without changes to the content under test, such as those based on the current date.
        # Because these errors can be unpredictable they behave differently than normal error codes:
        #  * They are not reported by default. The `--enable-optional-errors` option must be used to display these errors.
        #  * They cannot be ignored. This is done to maintain the integrity of the ignore system.
        self.optional_error_codes: set[str] = set()

    @property
    def error_code(self) -> t.Optional[str]:
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return None

    @property
    def can_ignore(self) -> bool:
        """True if the test supports ignore entries."""
        return True

    @property
    def can_skip(self) -> bool:
        """True if the test supports skip entries."""
        return not self.all_targets and not self.no_targets

    @property
    def all_targets(self) -> bool:
        """True if test targets will not be filtered using includes, excludes, requires or changes. Mutually exclusive with no_targets."""
        return False

    @property
    def no_targets(self) -> bool:
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return False

    @property
    def include_directories(self) -> bool:
        """True if the test targets should include directories."""
        return False

    @property
    def include_symlinks(self) -> bool:
        """True if the test targets should include symlinks."""
        return False

    @property
    def py2_compat(self) -> bool:
        """True if the test only applies to code that runs on Python 2.x."""
        return False

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return CONTROLLER_PYTHON_VERSIONS

    def origin_hook(self, args: SanityConfig) -> None:
        """This method is called on the origin, before the test runs or delegation occurs."""

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:  # pylint: disable=unused-argument
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        if self.no_targets:
            return []

        raise NotImplementedError('Sanity test "%s" must implement "filter_targets" or set "no_targets" to True.' % self.name)

    def filter_targets_by_version(self, args: SanityConfig, targets: list[TestTarget], python_version: str) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test, taking into account the Python version."""
        del python_version  # python_version is not used here, but derived classes may make use of it

        targets = self.filter_targets(targets)

        if self.py2_compat:
            # This sanity test is a Python 2.x compatibility test.
            content_config = get_content_config(args)

            if content_config.py2_support:
                # This collection supports Python 2.x.
                # Filter targets to include only those that require support for remote-only Python versions.
                targets = self.filter_remote_targets(targets)
            else:
                # This collection does not support Python 2.x.
                # There are no targets to test.
                targets = []

        return targets

    @staticmethod
    def filter_remote_targets(targets: list[TestTarget]) -> list[TestTarget]:
        """Return a filtered list of the given targets, including only those that require support for remote-only Python versions."""
        targets = [target for target in targets if (
            is_subdir(target.path, data_context().content.module_path) or
            is_subdir(target.path, data_context().content.module_utils_path) or
            is_subdir(target.path, data_context().content.unit_module_path) or
            is_subdir(target.path, data_context().content.unit_module_utils_path) or
            # include modules/module_utils within integration test library directories
            re.search('^%s/.*/library/' % re.escape(data_context().content.integration_targets_path), target.path) or
            # special handling for content in ansible-core
            (data_context().content.is_ansible and (
                # utility code that runs in target environments and requires support for remote-only Python versions
                is_subdir(target.path, 'test/lib/ansible_test/_util/target/') or
                # integration test support modules/module_utils continue to require support for remote-only Python versions
                re.search('^test/support/integration/.*/(modules|module_utils)/', target.path) or
                # collection loader requires support for remote-only Python versions
                re.search('^lib/ansible/utils/collection_loader/', target.path)
            ))
        )]

        return targets


class SanitySingleVersion(SanityTest, metaclass=abc.ABCMeta):
    """Base class for sanity test plugins which should run on a single python version."""

    @property
    def require_libyaml(self) -> bool:
        """True if the test requires PyYAML to have libyaml support."""
        return False

    @abc.abstractmethod
    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        """Run the sanity test and return the result."""

    def load_processor(self, args: SanityConfig) -> SanityIgnoreProcessor:
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)


class SanityCodeSmellTest(SanitySingleVersion):
    """Sanity test script."""

    def __init__(self, path) -> None:
        name = os.path.splitext(os.path.basename(path))[0]
        config_path = os.path.splitext(path)[0] + '.json'

        super().__init__(name=name)

        self.path = path
        self.config_path = config_path if os.path.exists(config_path) else None
        self.config = None

        if self.config_path:
            self.config = read_json_file(self.config_path)

        if self.config:
            self.enabled = not self.config.get('disabled')

            self.output: t.Optional[str] = self.config.get('output')
            self.extensions: list[str] = self.config.get('extensions')
            self.prefixes: list[str] = self.config.get('prefixes')
            self.files: list[str] = self.config.get('files')
            self.text: t.Optional[bool] = self.config.get('text')
            self.ignore_self: bool = self.config.get('ignore_self')
            self.minimum_python_version: t.Optional[str] = self.config.get('minimum_python_version')
            self.maximum_python_version: t.Optional[str] = self.config.get('maximum_python_version')

            self.__all_targets: bool = self.config.get('all_targets')
            self.__no_targets: bool = self.config.get('no_targets')
            self.__include_directories: bool = self.config.get('include_directories')
            self.__include_symlinks: bool = self.config.get('include_symlinks')
            self.__py2_compat: bool = self.config.get('py2_compat', False)
        else:
            self.output = None
            self.extensions = []
            self.prefixes = []
            self.files = []
            self.text = None
            self.ignore_self = False
            self.minimum_python_version = None
            self.maximum_python_version = None

            self.__all_targets = False
            self.__no_targets = True
            self.__include_directories = False
            self.__include_symlinks = False
            self.__py2_compat = False

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
    def all_targets(self) -> bool:
        """True if test targets will not be filtered using includes, excludes, requires or changes. Mutually exclusive with no_targets."""
        return self.__all_targets

    @property
    def no_targets(self) -> bool:
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return self.__no_targets

    @property
    def include_directories(self) -> bool:
        """True if the test targets should include directories."""
        return self.__include_directories

    @property
    def include_symlinks(self) -> bool:
        """True if the test targets should include symlinks."""
        return self.__include_symlinks

    @property
    def py2_compat(self) -> bool:
        """True if the test only applies to code that runs on Python 2.x."""
        return self.__py2_compat

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        versions = super().supported_python_versions

        if self.minimum_python_version:
            versions = tuple(version for version in versions if str_to_version(version) >= str_to_version(self.minimum_python_version))

        if self.maximum_python_version:
            versions = tuple(version for version in versions if str_to_version(version) <= str_to_version(self.maximum_python_version))

        return versions

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
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

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        """Run the sanity test and return the result."""
        cmd = [python.path, self.path]

        env = ansible_environment(args, color=False)
        env.update(PYTHONUTF8='1')  # force all code-smell sanity tests to run with Python UTF-8 Mode enabled

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
                raise ApplicationError('Unsupported output type: %s' % self.output)

        if not self.no_targets:
            data = '\n'.join(paths)

            if data:
                display.info(data, verbosity=4)

        try:
            stdout, stderr = intercept_python(args, python, cmd, data=data, env=env, capture=True)
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
            summary = '%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
            return SanityFailure(self.name, summary=summary)

        messages = settings.process_errors([], paths)

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)

    def load_processor(self, args: SanityConfig) -> SanityIgnoreProcessor:
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)


class SanityVersionNeutral(SanityTest, metaclass=abc.ABCMeta):
    """Base class for sanity test plugins which are idependent of the python version being used."""

    @abc.abstractmethod
    def test(self, args: SanityConfig, targets: SanityTargets) -> TestResult:
        """Run the sanity test and return the result."""

    def load_processor(self, args: SanityConfig) -> SanityIgnoreProcessor:
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, None)

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return None


class SanityMultipleVersion(SanityTest, metaclass=abc.ABCMeta):
    """Base class for sanity test plugins which should run on multiple python versions."""

    @abc.abstractmethod
    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        """Run the sanity test and return the result."""

    def load_processor(self, args: SanityConfig, python_version: str) -> SanityIgnoreProcessor:
        """Load the ignore processor for this sanity test."""
        return SanityIgnoreProcessor(args, self, python_version)

    @property
    def needs_pypi(self) -> bool:
        """True if the test requires PyPI, otherwise False."""
        return False

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return SUPPORTED_PYTHON_VERSIONS

    def filter_targets_by_version(self, args: SanityConfig, targets: list[TestTarget], python_version: str) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test, taking into account the Python version."""
        if not python_version:
            raise Exception('python_version is required to filter multi-version tests')

        targets = super().filter_targets_by_version(args, targets, python_version)

        if python_version in REMOTE_ONLY_PYTHON_VERSIONS:
            content_config = get_content_config(args)

            if python_version not in content_config.modules.python_versions:
                # when a remote-only python version is not supported there are no paths to test
                return []

            # when a remote-only python version is supported, tests must be applied only to targets that support remote-only Python versions
            targets = self.filter_remote_targets(targets)

        return targets


@cache
def sanity_get_tests() -> tuple[SanityTest, ...]:
    """Return a tuple of the available sanity tests."""
    import_plugins('commands/sanity')
    sanity_plugins: dict[str, t.Type[SanityTest]] = {}
    load_plugins(SanityTest, sanity_plugins)
    sanity_plugins.pop('sanity')  # SanityCodeSmellTest
    sanity_tests = tuple(plugin() for plugin in sanity_plugins.values() if data_context().content.is_ansible or not plugin.ansible_only)
    sanity_tests = tuple(sorted(sanity_tests + collect_code_smell_tests(), key=lambda k: k.name))
    return sanity_tests


def create_sanity_virtualenv(
    args: SanityConfig,
    python: PythonConfig,
    name: str,
    coverage: bool = False,
    minimize: bool = False,
) -> t.Optional[VirtualPythonConfig]:
    """Return an existing sanity virtual environment matching the requested parameters or create a new one."""
    commands = collect_requirements(  # create_sanity_virtualenv()
        python=python,
        controller=True,
        virtualenv=False,
        command=None,
        ansible=False,
        cryptography=False,
        coverage=coverage,
        minimize=minimize,
        sanity=name,
    )

    if commands:
        label = f'sanity.{name}'
    else:
        label = 'sanity'  # use a single virtualenv name for tests which have no requirements

    # The path to the virtual environment must be kept short to avoid the 127 character shebang length limit on Linux.
    # If the limit is exceeded, generated entry point scripts from pip installed packages will fail with syntax errors.
    virtualenv_install = json.dumps([command.serialize() for command in commands], indent=4)
    virtualenv_hash = hash_pip_commands(commands)
    virtualenv_cache = os.path.join(os.path.expanduser('~/.ansible/test/venv'))
    virtualenv_path = os.path.join(virtualenv_cache, label, f'{python.version}', virtualenv_hash)
    virtualenv_marker = os.path.join(virtualenv_path, 'marker.txt')

    meta_install = os.path.join(virtualenv_path, 'meta.install.json')
    meta_yaml = os.path.join(virtualenv_path, 'meta.yaml.json')

    virtualenv_python = VirtualPythonConfig(
        version=python.version,
        path=os.path.join(virtualenv_path, 'bin', 'python'),
    )

    if not os.path.exists(virtualenv_marker):
        # a virtualenv without a marker is assumed to have been partially created
        remove_tree(virtualenv_path)

        if not create_virtual_environment(args, python, virtualenv_path):
            return None

        run_pip(args, virtualenv_python, commands, None)  # create_sanity_virtualenv()

        write_text_file(meta_install, virtualenv_install)

        # false positive: pylint: disable=no-member
        if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
            virtualenv_yaml = yamlcheck(virtualenv_python)
        else:
            virtualenv_yaml = None

        write_json_file(meta_yaml, virtualenv_yaml)

        created_venvs.append(f'{label}-{python.version}')

    # touch the marker to keep track of when the virtualenv was last used
    pathlib.Path(virtualenv_marker).touch()

    return virtualenv_python


def hash_pip_commands(commands: list[PipCommand]) -> str:
    """Return a short hash unique to the given list of pip commands, suitable for identifying the resulting sanity test environment."""
    serialized_commands = json.dumps([make_pip_command_hashable(command) for command in commands], indent=4)

    return hashlib.sha256(to_bytes(serialized_commands)).hexdigest()[:8]


def make_pip_command_hashable(command: PipCommand) -> tuple[str, dict[str, t.Any]]:
    """Return a serialized version of the given pip command that is suitable for hashing."""
    if isinstance(command, PipInstall):
        # The pre-build instructions for pip installs must be omitted, so they do not affect the hash.
        # This is allows the pre-build commands to be added without breaking sanity venv caching.
        # It is safe to omit these from the hash since they only affect packages used during builds, not what is installed in the venv.
        command = PipInstall(
            requirements=[omit_pre_build_from_requirement(*req) for req in command.requirements],
            constraints=list(command.constraints),
            packages=list(command.packages),
        )

    return command.serialize()


def omit_pre_build_from_requirement(path: str, requirements: str) -> tuple[str, str]:
    """Return the given requirements with pre-build instructions omitted."""
    lines = requirements.splitlines(keepends=True)

    # CAUTION: This code must be kept in sync with the code which processes pre-build instructions in:
    #          test/lib/ansible_test/_util/target/setup/requirements.py
    lines = [line for line in lines if not line.startswith('# pre-build ')]

    return path, ''.join(lines)


def check_sanity_virtualenv_yaml(python: VirtualPythonConfig) -> t.Optional[bool]:
    """Return True if PyYAML has libyaml support for the given sanity virtual environment, False if it does not and None if it was not found."""
    virtualenv_path = os.path.dirname(os.path.dirname(python.path))
    meta_yaml = os.path.join(virtualenv_path, 'meta.yaml.json')
    virtualenv_yaml = read_json_file(meta_yaml)

    return virtualenv_yaml
