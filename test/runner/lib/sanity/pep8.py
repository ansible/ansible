"""Sanity test for PEP 8 style guidelines using pycodestyle."""
from __future__ import absolute_import, print_function

import os
import re

from lib.sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
)

from lib.util import (
    SubprocessError,
    display,
    run_command,
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    calculate_best_confidence,
)

PEP8_SKIP_PATH = 'test/sanity/pep8/skip.txt'
PEP8_LEGACY_PATH = 'test/sanity/pep8/legacy-files.txt'


class Pep8Test(SanitySingleVersion):
    """Sanity test for PEP 8 style guidelines using pycodestyle."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        with open(PEP8_SKIP_PATH, 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()

        with open(PEP8_LEGACY_PATH, 'r') as legacy_fd:
            legacy_paths = legacy_fd.read().splitlines()

        with open('test/sanity/pep8/legacy-ignore.txt', 'r') as ignore_fd:
            legacy_ignore = set(ignore_fd.read().splitlines())

        with open('test/sanity/pep8/current-ignore.txt', 'r') as ignore_fd:
            current_ignore = sorted(ignore_fd.read().splitlines())

        skip_paths_set = set(skip_paths)
        legacy_paths_set = set(legacy_paths)

        paths = sorted(i.path for i in targets.include if (os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/')) and i.path not in skip_paths_set)

        cmd = [
            args.python_executable,
            '-m', 'pycodestyle',
            '--max-line-length', '160',
            '--config', '/dev/null',
            '--ignore', ','.join(sorted(current_ignore)),
        ] + paths

        if paths:
            try:
                stdout, stderr = run_command(args, cmd, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
        else:
            stdout = None

        if args.explain:
            return SanitySuccess(self.name)

        if stdout:
            pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[WE][0-9]{3}) (?P<message>.*)$'

            results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]
        else:
            results = []

        results = [SanityMessage(
            message=r['message'],
            path=r['path'],
            line=int(r['line']),
            column=int(r['column']),
            level='warning' if r['code'].startswith('W') else 'error',
            code=r['code'],
        ) for r in results]

        failed_result_paths = set([result.path for result in results])
        used_paths = set(paths)

        errors = []
        summary = {}

        line = 0

        for path in legacy_paths:
            line += 1

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                errors.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=PEP8_LEGACY_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PEP8_LEGACY_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

            if path in used_paths and path not in failed_result_paths:
                # Keep files out of the list which no longer require the relaxed rule set.
                errors.append(SanityMessage(
                    code='A201',
                    message='Remove "%s" since it passes the current rule set' % path,
                    path=PEP8_LEGACY_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PEP8_LEGACY_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        line = 0

        for path in skip_paths:
            line += 1

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                errors.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=PEP8_SKIP_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PEP8_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        for result in results:
            if result.path in legacy_paths_set and result.code in legacy_ignore:
                # Files on the legacy list are permitted to have errors on the legacy ignore list.
                # However, we want to report on their existence to track progress towards eliminating these exceptions.
                display.info('PEP 8: %s (legacy)' % result, verbosity=3)

                key = '%s %s' % (result.code, re.sub('[0-9]+', 'NNN', result.message))

                if key not in summary:
                    summary[key] = 0

                summary[key] += 1
            else:
                # Files not on the legacy list and errors not on the legacy ignore list are PEP 8 policy errors.
                errors.append(result)

        if summary:
            lines = []
            count = 0

            for key in sorted(summary):
                count += summary[key]
                lines.append('PEP 8: %5d %s' % (summary[key], key))

            display.info('PEP 8: There were %d different legacy issues found (%d total):' % (len(summary), count), verbosity=1)
            display.info('PEP 8: Count Code Message', verbosity=1)

            for line in lines:
                display.info(line, verbosity=1)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
