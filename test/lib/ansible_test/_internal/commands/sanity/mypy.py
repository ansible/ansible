"""Sanity test which executes mypy."""
from __future__ import annotations

import dataclasses
import os
import re
import typing as t

from . import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    SanityTargets,
    create_sanity_virtualenv,
)

from ...constants import (
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_ONLY_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from ...test import (
    TestResult,
)

from ...target import (
    TestTarget,
)

from ...util import (
    SubprocessError,
    display,
    parse_to_list_of_dict,
    ANSIBLE_TEST_CONTROLLER_ROOT,
    ApplicationError,
    is_subdir,
    str_to_version,
)

from ...util_common import (
    intercept_python,
)

from ...ansible_util import (
    ansible_environment,
)

from ...config import (
    SanityConfig,
)

from ...host_configs import (
    PythonConfig,
    VirtualPythonConfig,
)


class MypyTest(SanityMultipleVersion):
    """Sanity test which executes mypy."""

    ansible_only = True

    vendored_paths = (
        'lib/ansible/module_utils/six/__init__.py',
        'lib/ansible/module_utils/distro/_distro.py',
        'lib/ansible/module_utils/compat/_selectors2.py',
    )

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' and target.path not in self.vendored_paths and (
                target.path.startswith('lib/ansible/') or target.path.startswith('test/lib/ansible_test/_internal/')
                or target.path.startswith('packaging/')
                or target.path.startswith('test/lib/ansible_test/_util/target/sanity/import/'))]

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        # mypy 0.981 dropped support for Python 2
        # see: https://mypy-lang.blogspot.com/2022/09/mypy-0981-released.html
        # cryptography dropped support for Python 3.5 in version 3.3
        # see: https://cryptography.io/en/latest/changelog/#v3-3
        return tuple(version for version in SUPPORTED_PYTHON_VERSIONS if str_to_version(version) >= (3, 6))

    @property
    def error_code(self) -> t.Optional[str]:
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    @property
    def needs_pypi(self) -> bool:
        """True if the test requires PyPI, otherwise False."""
        return True

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        settings = self.load_processor(args, python.version)

        paths = [target.path for target in targets.include]

        virtualenv_python = create_sanity_virtualenv(args, args.controller_python, self.name)

        if args.prime_venvs:
            return SanitySkipped(self.name, python_version=python.version)

        if not virtualenv_python:
            display.warning(f'Skipping sanity test "{self.name}" due to missing virtual environment support on Python {args.controller_python.version}.')
            return SanitySkipped(self.name, python.version)

        controller_python_versions = CONTROLLER_PYTHON_VERSIONS
        remote_only_python_versions = REMOTE_ONLY_PYTHON_VERSIONS

        contexts = (
            MyPyContext('ansible-test', ['test/lib/ansible_test/_util/target/sanity/import/'], controller_python_versions),
            MyPyContext('ansible-test', ['test/lib/ansible_test/_internal/'], controller_python_versions),
            MyPyContext('ansible-core', ['lib/ansible/'], controller_python_versions),
            MyPyContext('modules', ['lib/ansible/modules/', 'lib/ansible/module_utils/'], remote_only_python_versions),
            MyPyContext('packaging', ['packaging/'], controller_python_versions),
        )

        unfiltered_messages: list[SanityMessage] = []

        for context in contexts:
            if python.version not in context.python_versions:
                continue

            unfiltered_messages.extend(self.test_context(args, virtualenv_python, python, context, paths))

        notices = []
        messages = []

        for message in unfiltered_messages:
            if message.level != 'error':
                notices.append(message)
                continue

            match = re.search(r'^(?P<message>.*) {2}\[(?P<code>.*)]$', message.message)

            messages.append(SanityMessage(
                message=match.group('message'),
                path=message.path,
                line=message.line,
                column=message.column,
                level=message.level,
                code=match.group('code'),
            ))

        for notice in notices:
            display.info(notice.format(), verbosity=3)

        # The following error codes from mypy indicate that results are incomplete.
        # That prevents the test from completing successfully, just as if mypy were to traceback or generate unexpected output.
        fatal_error_codes = {
            'import',
            'syntax',
        }

        fatal_errors = [message for message in messages if message.code in fatal_error_codes]

        if fatal_errors:
            error_message = '\n'.join(error.format() for error in fatal_errors)
            raise ApplicationError(f'Encountered {len(fatal_errors)} fatal errors reported by mypy:\n{error_message}')

        paths_set = set(paths)

        # Only report messages for paths that were specified as targets.
        # Imports in our code are followed by mypy in order to perform its analysis, which is important for accurate results.
        # However, it will also report issues on those files, which is not the desired behavior.
        messages = [message for message in messages if message.path in paths_set]

        if args.explain:
            return SanitySuccess(self.name, python_version=python.version)

        results = settings.process_errors(messages, paths)

        if results:
            return SanityFailure(self.name, messages=results, python_version=python.version)

        return SanitySuccess(self.name, python_version=python.version)

    @staticmethod
    def test_context(
        args: SanityConfig,
        virtualenv_python: VirtualPythonConfig,
        python: PythonConfig,
        context: MyPyContext,
        paths: list[str],
    ) -> list[SanityMessage]:
        """Run mypy tests for the specified context."""
        context_paths = [path for path in paths if any(is_subdir(path, match_path) for match_path in context.paths)]

        if not context_paths:
            return []

        config_path = os.path.join(ANSIBLE_TEST_CONTROLLER_ROOT, 'sanity', 'mypy', f'{context.name}.ini')

        display.info(f'Checking context "{context.name}"', verbosity=1)

        env = ansible_environment(args, color=False)
        env['MYPYPATH'] = env['PYTHONPATH']

        # The --no-site-packages option should not be used, as it will prevent loading of type stubs from the sanity test virtual environment.

        # Enabling the --warn-unused-configs option would help keep the config files clean.
        # However, the option can only be used when all files in tested contexts are evaluated.
        # Unfortunately sanity tests have no way of making that determination currently.
        # The option is also incompatible with incremental mode and caching.

        cmd = [
            # Below are arguments common to all contexts.
            # They are kept here to avoid repetition in each config file.
            virtualenv_python.path,
            '-m', 'mypy',
            '--show-column-numbers',
            '--show-error-codes',
            '--no-error-summary',
            # This is a fairly common pattern in our code, so we'll allow it.
            '--allow-redefinition',
            # Since we specify the path(s) to test, it's important that mypy is configured to use the default behavior of following imports.
            '--follow-imports', 'normal',
            # Incremental results and caching do not provide significant performance benefits.
            # It also prevents the use of the --warn-unused-configs option.
            '--no-incremental',
            '--cache-dir', '/dev/null',
            # The platform is specified here so that results are consistent regardless of what platform the tests are run from.
            # In the future, if testing of other platforms is desired, the platform should become part of the test specification, just like the Python version.
            '--platform', 'linux',
            # Despite what the documentation [1] states, the --python-version option does not cause mypy to search for a corresponding Python executable.
            # It will instead use the Python executable that is used to run mypy itself.
            # The --python-executable option can be used to specify the Python executable, with the default being the executable used to run mypy.
            # As a precaution, that option is used in case the behavior of mypy is updated in the future to match the documentation.
            # That should help guarantee that the Python executable providing type hints is the one used to run mypy.
            # [1] https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-python-version
            '--python-executable', virtualenv_python.path,
            '--python-version', python.version,
            # Below are context specific arguments.
            # They are primarily useful for listing individual 'ignore_missing_imports' entries instead of using a global ignore.
            '--config-file', config_path,
        ]  # fmt: skip

        cmd.extend(context_paths)

        try:
            stdout, stderr = intercept_python(args, virtualenv_python, cmd, env, capture=True)

            if stdout or stderr:
                raise SubprocessError(cmd, stdout=stdout, stderr=stderr)
        except SubprocessError as ex:
            if ex.status != 1 or ex.stderr or not ex.stdout:
                raise

            stdout = ex.stdout

        pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):((?P<column>[0-9]+):)? (?P<level>[^:]+): (?P<message>.*)$'

        parsed = parse_to_list_of_dict(pattern, stdout or '')

        messages = [SanityMessage(
            level=r['level'],
            message=r['message'],
            path=r['path'],
            line=int(r['line']),
            column=int(r.get('column') or '0'),
        ) for r in parsed]

        return messages


@dataclasses.dataclass(frozen=True)
class MyPyContext:
    """Context details for a single run of mypy."""

    name: str
    paths: list[str]
    python_versions: tuple[str, ...]
