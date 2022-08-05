"""Sanity test for proper python syntax."""
from __future__ import annotations

import os

from . import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SanitySkipped,
    TARGET_SANITY_ROOT,
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
    is_subdir,
)

from ...util_common import (
    run_command,
)

from ...config import (
    SanityConfig,
)

from ...host_configs import (
    PythonConfig,
)


class CompileTest(SanityMultipleVersion):
    """Sanity test for proper python syntax."""
    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' or is_subdir(target.path, 'bin')]

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        if args.prime_venvs:
            return SanitySkipped(self.name, python_version=python.version)

        settings = self.load_processor(args, python.version)

        paths = [target.path for target in targets.include]

        cmd = [python.path, os.path.join(TARGET_SANITY_ROOT, 'compile', 'compile.py')]

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
            return SanitySuccess(self.name, python_version=python.version)

        pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

        results = parse_to_list_of_dict(pattern, stdout)

        results = [SanityMessage(
            message=r['message'],
            path=r['path'].replace('./', ''),
            line=int(r['line']),
            column=int(r['column']),
        ) for r in results]

        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results, python_version=python.version)

        return SanitySuccess(self.name, python_version=python.version)
