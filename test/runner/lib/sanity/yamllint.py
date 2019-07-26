"""Sanity test using yamllint."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os

import lib.types as t

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
    ANSIBLE_ROOT,
    is_subdir,
    find_python,
)

from lib.util_common import (
    run_command,
)

from lib.config import (
    SanityConfig,
)

from lib.data import (
    data_context,
)


class YamllintTest(SanitySingleVersion):
    """Sanity test using yamllint."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        settings = self.load_processor(args)

        paths = [i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml')]

        for plugin_type, plugin_path in sorted(data_context().content.plugin_paths.items()):
            if plugin_type == 'module_utils':
                continue

            paths.extend([target.path for target in targets.include if
                          os.path.splitext(target.path)[1] == '.py' and
                          os.path.basename(target.path) != '__init__.py' and
                          is_subdir(target.path, plugin_path)])

        paths = settings.filter_skipped_paths(paths)

        if not paths:
            return SanitySkipped(self.name)

        python = find_python(python_version)

        results = self.test_paths(args, paths, python)
        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)

    @staticmethod
    def test_paths(args, paths, python):
        """
        :type args: SanityConfig
        :type paths: list[str]
        :type python: str
        :rtype: list[SanityMessage]
        """
        cmd = [
            python,
            os.path.join(ANSIBLE_ROOT, 'test/sanity/yamllint/yamllinter.py'),
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
