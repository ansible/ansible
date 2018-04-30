"""Sanity test for proper python syntax."""
from __future__ import absolute_import, print_function

import os
import re

from lib.sanity import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
)

from lib.util import (
    SubprocessError,
    run_command,
    display,
    find_python,
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    calculate_best_confidence,
)


class CompileTest(SanityMultipleVersion):
    """Sanity test for proper python syntax."""
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        # optional list of regex patterns to exclude from tests
        skip_file = 'test/sanity/compile/python%s-skip.txt' % python_version

        if os.path.exists(skip_file):
            with open(skip_file, 'r') as skip_fd:
                skip_paths = skip_fd.read().splitlines()
        else:
            skip_paths = []

        paths = sorted(i.path for i in targets.include if (os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/')) and i.path not in skip_paths)

        if not paths:
            return SanitySkipped(self.name, python_version=python_version)

        cmd = [find_python(python_version), 'test/sanity/compile/compile.py']

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
            return SanitySuccess(self.name, python_version=python_version)

        pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

        results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

        results = [SanityMessage(
            message=r['message'],
            path=r['path'].replace('./', ''),
            line=int(r['line']),
            column=int(r['column']),
        ) for r in results]

        line = 0

        for path in skip_paths:
            line += 1

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                results.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=skip_file,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((skip_file, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        if results:
            return SanityFailure(self.name, messages=results, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)
