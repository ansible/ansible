"""Sanity test using yamllint."""
from __future__ import annotations

import json
import os
import typing as t

from . import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SANITY_ROOT,
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
    is_subdir,
)

from ...util_common import (
    run_command,
)

from ...config import (
    SanityConfig,
)

from ...data import (
    data_context,
)

from ...host_configs import (
    PythonConfig,
)


class YamllintTest(SanitySingleVersion):
    """Sanity test using yamllint."""

    @property
    def error_code(self) -> t.Optional[str]:
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    @property
    def require_libyaml(self) -> bool:
        """True if the test requires PyYAML to have libyaml support."""
        return True

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        yaml_targets = [target for target in targets if os.path.splitext(target.path)[1] in ('.yml', '.yaml')]

        for plugin_type, plugin_path in sorted(data_context().content.plugin_paths.items()):
            if plugin_type == 'module_utils':
                continue

            yaml_targets.extend([target for target in targets if
                                 os.path.splitext(target.path)[1] == '.py' and
                                 os.path.basename(target.path) != '__init__.py' and
                                 is_subdir(target.path, plugin_path)])

        return yaml_targets

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        results = self.test_paths(args, paths, python)
        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)

    @staticmethod
    def test_paths(args: SanityConfig, paths: list[str], python: PythonConfig) -> list[SanityMessage]:
        """Test the specified paths using the given Python and return the results."""
        cmd = [
            python.path,
            os.path.join(SANITY_ROOT, 'yamllint', 'yamllinter.py'),
        ]

        data = '\n'.join(paths)

        display.info(data, verbosity=4)

        try:
            stdout, stderr = run_command(args, cmd, data=data, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr:
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return []

        results = json.loads(stdout)['messages']

        results = [SanityMessage(
            code=r['code'],
            message=r['message'],
            path=r['path'],
            line=int(r['line']),
            column=int(r['column']),
            level=r['level'],
        ) for r in results]

        return results
