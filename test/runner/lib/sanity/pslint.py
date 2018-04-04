"""Sanity test using PSScriptAnalyzer."""
from __future__ import absolute_import, print_function

import collections
import json
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

from lib.test import (
    calculate_confidence,
    calculate_best_confidence,
)

PSLINT_SKIP_PATH = 'test/sanity/pslint/skip.txt'
PSLINT_IGNORE_PATH = 'test/sanity/pslint/ignore.txt'


class PslintTest(SanitySingleVersion):
    """Sanity test using PSScriptAnalyzer."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        with open(PSLINT_SKIP_PATH, 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()

        invalid_ignores = []

        with open(PSLINT_IGNORE_PATH, 'r') as ignore_fd:
            ignore_entries = ignore_fd.read().splitlines()
            ignore = collections.defaultdict(dict)
            line = 0

            for ignore_entry in ignore_entries:
                line += 1

                if ' ' not in ignore_entry:
                    invalid_ignores.append((line, 'Invalid syntax'))
                    continue

                path, code = ignore_entry.split(' ', 1)

                if not os.path.exists(path):
                    invalid_ignores.append((line, 'Remove "%s" since it does not exist' % path))
                    continue

                ignore[path][code] = line

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.ps1', '.psm1', '.psd1') and i.path not in skip_paths)

        if not paths:
            return SanitySkipped(self.name)

        if not find_executable('pwsh', required='warning'):
            return SanitySkipped(self.name)

        cmd = ['test/sanity/pslint/pslint.ps1'] + paths

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

        severity = [
            'Information',
            'Warning',
            'Error',
        ]

        cwd = os.getcwd() + '/'

        # replace unicode smart quotes with ascii versions
        stdout = re.sub(u'[\u2018\u2019]', "'", stdout)
        stdout = re.sub(u'[\u201c\u201d]', '"', stdout)

        messages = json.loads(stdout)

        errors = [SanityMessage(
            code=m['RuleName'],
            message=m['Message'],
            path=m['ScriptPath'].replace(cwd, ''),
            line=m['Line'] or 0,
            column=m['Column'] or 0,
            level=severity[m['Severity']],
        ) for m in messages]

        line = 0

        filtered = []

        for error in errors:
            if error.code in ignore[error.path]:
                ignore[error.path][error.code] = None  # error ignored, clear line number of ignore entry to track usage
            else:
                filtered.append(error)  # error not ignored

        errors = filtered

        for invalid_ignore in invalid_ignores:
            errors.append(SanityMessage(
                code='A201',
                message=invalid_ignore[1],
                path=PSLINT_IGNORE_PATH,
                line=invalid_ignore[0],
                column=1,
                confidence=calculate_confidence(PSLINT_IGNORE_PATH, line, args.metadata) if args.metadata.changes else None,
            ))

        for path in skip_paths:
            line += 1

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                errors.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=PSLINT_SKIP_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PSLINT_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        for path in paths:
            if path not in ignore:
                continue

            for code in ignore[path]:
                line = ignore[path][code]

                if not line:
                    continue

                errors.append(SanityMessage(
                    code='A102',
                    message='Remove since "%s" passes "%s" test' % (path, code),
                    path=PSLINT_IGNORE_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PSLINT_IGNORE_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
