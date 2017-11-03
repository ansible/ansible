"""Sanity test using pylint."""
from __future__ import absolute_import, print_function

import json
import os
import datetime

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
    display,
    find_executable,
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

UNSUPPORTED_PYTHON_VERSIONS = (
    '2.6',
)


class PylintTest(SanitySingleVersion):
    """Sanity test using pylint."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: SanityResult
        """
        if args.python_version in UNSUPPORTED_PYTHON_VERSIONS:
            display.warning('Skipping pylint on unsupported Python version %s.' % args.python_version)
            return SanitySkipped(self.name)

        with open(PYLINT_SKIP_PATH, 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()

        skip_paths_set = set(skip_paths)

        paths = sorted(i.path for i in targets.include if (os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/')) and i.path not in skip_paths_set)

        contexts = {}
        remaining_paths = set(paths)

        def add_context(available_paths, context_name, context_filter):
            """
            :type available_paths: set[str]
            :type context_name: str
            :type context_filter: (str) -> bool
            """
            filtered_paths = set(p for p in available_paths if context_filter(p))
            contexts[context_name] = sorted(filtered_paths)
            available_paths -= filtered_paths

        add_context(remaining_paths, 'ansible-test', lambda p: p.startswith('test/runner/'))
        add_context(remaining_paths, 'units', lambda p: p.startswith('test/units/'))
        add_context(remaining_paths, 'test', lambda p: p.startswith('test/'))
        add_context(remaining_paths, 'hacking', lambda p: p.startswith('hacking/'))
        add_context(remaining_paths, 'modules', lambda p: p.startswith('lib/ansible/modules/'))
        add_context(remaining_paths, 'module_utils', lambda p: p.startswith('lib/ansible/module_utils/'))
        add_context(remaining_paths, 'ansible', lambda p: True)

        messages = []
        context_times = []

        test_start = datetime.datetime.utcnow()

        for context in sorted(contexts):
            context_paths = contexts[context]

            if not context_paths:
                continue

            context_start = datetime.datetime.utcnow()
            messages += self.pylint(args, context, context_paths)
            context_end = datetime.datetime.utcnow()

            context_times.append('%s: %d (%s)' % (context, len(context_paths), context_end - context_start))

        test_end = datetime.datetime.utcnow()

        for context_time in context_times:
            display.info(context_time, verbosity=4)

        display.info('total: %d (%s)' % (len(paths), test_end - test_start), verbosity=4)

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

    def pylint(self, args, context, paths):
        """
        :type args: SanityConfig
        :param context: str
        :param paths: list[str]
        :return: list[dict[str, str]]
        """
        rcfile = 'test/sanity/pylint/config/%s' % context

        if not os.path.exists(rcfile):
            rcfile = 'test/sanity/pylint/config/default'

        cmd = [
            'python%s' % args.python_version,
            find_executable('pylint'),
            '--jobs', '0',
            '--reports', 'n',
            '--max-line-length', '160',
            '--rcfile', rcfile,
            '--output-format', 'json',
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

        if not args.explain and stdout:
            messages = json.loads(stdout)
        else:
            messages = []

        return messages
