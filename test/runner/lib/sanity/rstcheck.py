"""Sanity test using rstcheck."""
from __future__ import absolute_import, print_function

import os

from lib.sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
)

from lib.util import (
    SubprocessError,
    run_command,
    parse_to_dict,
    display,
    find_executable,
)

from lib.config import (
    SanityConfig,
)

UNSUPPORTED_PYTHON_VERSIONS = (
    '2.6',
)


class RstcheckTest(SanitySingleVersion):
    """Sanity test using rstcheck."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        if args.python_version in UNSUPPORTED_PYTHON_VERSIONS:
            display.warning('Skipping rstcheck on unsupported Python version %s.' % args.python_version)
            return SanitySkipped(self.name)

        with open('test/sanity/rstcheck/ignore-substitutions.txt', 'r') as ignore_fd:
            ignore_substitutions = sorted(set(ignore_fd.read().splitlines()))

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.rst',))

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            args.python_executable,
            '-m', 'rstcheck',
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
            return SanitySuccess(self.name)

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
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
