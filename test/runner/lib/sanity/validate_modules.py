"""Sanity test using validate-modules."""
from __future__ import absolute_import, print_function

import collections
import json
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
    display,
    run_command,
    read_lines_without_comments,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    calculate_confidence,
    calculate_best_confidence,
)

VALIDATE_SKIP_PATH = 'test/sanity/validate-modules/skip.txt'
VALIDATE_IGNORE_PATH = 'test/sanity/validate-modules/ignore.txt'


class ValidateModulesTest(SanitySingleVersion):
    """Sanity test using validate-modules."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        skip_paths = read_lines_without_comments(VALIDATE_SKIP_PATH)
        skip_paths_set = set(skip_paths)

        env = ansible_environment(args, color=False)

        paths = sorted([i.path for i in targets.include if i.module and i.path not in skip_paths_set])

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            args.python_executable,
            'test/sanity/validate-modules/validate-modules',
            '--format', 'json',
            '--arg-spec',
        ] + paths

        invalid_ignores = []

        ignore_entries = read_lines_without_comments(VALIDATE_IGNORE_PATH)
        ignore = collections.defaultdict(dict)
        line = 0

        for ignore_entry in ignore_entries:
            line += 1

            if not ignore_entry:
                continue

            if ' ' not in ignore_entry:
                invalid_ignores.append((line, 'Invalid syntax'))
                continue

            path, code = ignore_entry.split(' ', 1)

            ignore[path][code] = line

        if args.base_branch:
            cmd.extend([
                '--base-branch', args.base_branch,
            ])
        else:
            display.warning('Cannot perform module comparison against the base branch. Base branch not detected when running locally.')

        try:
            stdout, stderr = run_command(args, cmd, env=env, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr or status not in (0, 3):
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        messages = json.loads(stdout)

        errors = []

        for filename in messages:
            output = messages[filename]

            for item in output['errors']:
                errors.append(SanityMessage(
                    path=filename,
                    line=int(item['line']) if 'line' in item else 0,
                    column=int(item['column']) if 'column' in item else 0,
                    level='error',
                    code='E%s' % item['code'],
                    message=item['msg'],
                ))

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
                path=VALIDATE_IGNORE_PATH,
                line=invalid_ignore[0],
                column=1,
                confidence=calculate_confidence(VALIDATE_IGNORE_PATH, line, args.metadata) if args.metadata.changes else None,
            ))

        line = 0

        for path in skip_paths:
            line += 1

            if not path:
                continue

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                errors.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=VALIDATE_SKIP_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((VALIDATE_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
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
                    path=VALIDATE_IGNORE_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((VALIDATE_IGNORE_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
