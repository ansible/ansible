"""Sanity test using yamllint."""
from __future__ import absolute_import, print_function

import os
import re

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
    find_executable,
)

from lib.config import (
    SanityConfig,
)


class YamllintTest(SanitySingleVersion):
    """Sanity test using yamllint."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: SanityResult
        """
        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml'))

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            'python%s' % args.python_version,
            find_executable('yamllint'),
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
            return SanitySuccess(self.name)

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
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
