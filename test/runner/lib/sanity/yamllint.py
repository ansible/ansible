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
<<<<<<< 7243a556be6049e08308b16674ee8d44d1925381
    display,
    ANSIBLE_ROOT,
    is_subdir,
)

from lib.util_common import (
=======
>>>>>>> Revert "Datadisk test"
    run_command,
    display,
)

from lib.config import (
    SanityConfig,
)

from lib.data import (
    data_context,
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
        ]

        for plugin_type, plugin_path in sorted(data_context().content.plugin_paths.items()):
            if plugin_type == 'module_utils':
                continue

            paths.append([target.path for target in targets.include if
                          os.path.splitext(target.path)[1] == '.py' and
                          os.path.basename(target.path) != '__init__.py' and
                          is_subdir(target.path, plugin_path)])

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
<<<<<<< 7243a556be6049e08308b16674ee8d44d1925381
            os.path.join(ANSIBLE_ROOT, 'test/sanity/yamllint/yamllinter.py'),
=======
            'test/sanity/yamllint/yamllinter.py',
>>>>>>> Revert "Datadisk test"
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
