"""Sanity test using pylint."""
from __future__ import absolute_import, print_function

import json
import os

from lib.sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
)

from lib.util import (
    SubprocessError,
    run_command,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    SanityConfig,
)

from lib.test import (
    calculate_best_confidence,
)

PYLINT_SKIP_PATH = 'test/sanity/pylint/skip.txt'


class PylintTest(SanitySingleVersion):
    """Sanity test using pylint."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: SanityResult
        """
        with open(PYLINT_SKIP_PATH, 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()

        with open('test/sanity/pylint/disable.txt', 'r') as disable_fd:
            disable = set(c for c in disable_fd.read().splitlines() if not c.strip().startswith('#'))

        with open('test/sanity/pylint/enable.txt', 'r') as enable_fd:
            enable = set(c for c in enable_fd.read().splitlines() if not c.strip().startswith('#'))

        skip_paths_set = set(skip_paths)

        paths = sorted(i.path for i in targets.include if (os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/')) and i.path not in skip_paths_set)

        cmd = [
            'pylint',
            '--jobs', '0',
            '--reports', 'n',
            '--max-line-length', '160',
            '--rcfile', '/dev/null',
            '--ignored-modules', '_MovedItems',
            '--output-format', 'json',
            '--disable', ','.join(sorted(disable)),
            '--enable', ','.join(sorted(enable)),
        ] + paths

        env = ansible_environment(args)

        if paths:
            try:
                stdout, stderr = run_command(args, cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr or status >= 32:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
        else:
            stdout = None

        if args.explain:
            return SanitySuccess(self.name)

        if stdout:
            messages = json.loads(stdout)
        else:
            messages = []

        errors = [SanityMessage(
            message=m['message'].replace('\n', ' '),
            path=m['path'],
            line=int(m['line']),
            column=int(m['column']),
            level=m['type'],
            code=m['symbol'],
        ) for m in messages]

        line = 0

        for path in skip_paths:
            line += 1

            if not os.path.exists(path):
                # Keep files out of the list which no longer exist in the repo.
                errors.append(SanityMessage(
                    code='A101',
                    message='Remove "%s" since it does not exist' % path,
                    path=PYLINT_SKIP_PATH,
                    line=line,
                    column=1,
                    confidence=calculate_best_confidence(((PYLINT_SKIP_PATH, line), (path, 0)), args.metadata) if args.metadata.changes else None,
                ))

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
