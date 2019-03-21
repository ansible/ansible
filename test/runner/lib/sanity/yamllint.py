"""Sanity test using yamllint."""
from __future__ import absolute_import, print_function

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
    run_command,
    display,
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
        :rtype: TestResult
        """
        paths = [
            [i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml')],

            [i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and
             os.path.basename(i.path) != '__init__.py' and
             i.path.startswith('lib/ansible/plugins/')],

            [i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and
             os.path.basename(i.path) != '__init__.py' and
             i.path.startswith('lib/ansible/modules/')],

            [i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and
             os.path.basename(i.path) != '__init__.py' and
             i.path.startswith('lib/ansible/plugins/doc_fragments/')],
        ]

        paths = [sorted(p) for p in paths if p]

        if not paths:
            return SanitySkipped(self.name)

        results = []

        for test_paths in paths:
            results += self.test_paths(args, test_paths)

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)

    @staticmethod
    def test_paths(args, paths):
        """
        :type args: SanityConfig
        :type paths: list[str]
        :rtype: list[SanityMessage]
        """
        cmd = [
            args.python_executable,
            'test/sanity/yamllint/yamllinter.py',
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
