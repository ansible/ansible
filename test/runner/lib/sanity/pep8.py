"""Sanity test for PEP 8 style guidelines using pycodestyle."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import lib.types as t

from lib.sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
)

from lib.util import (
    SubprocessError,
    read_lines_without_comments,
    parse_to_list_of_dict,
    ANSIBLE_ROOT,
    find_python,
)

from lib.util_common import (
    run_command,
)

from lib.config import (
    SanityConfig,
)


class Pep8Test(SanitySingleVersion):
    """Sanity test for PEP 8 style guidelines using pycodestyle."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'A100'

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        current_ignore_file = os.path.join(ANSIBLE_ROOT, 'test/sanity/pep8/current-ignore.txt')
        current_ignore = sorted(read_lines_without_comments(current_ignore_file, remove_blank_lines=True))

        settings = self.load_processor(args)

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/'))
        paths = settings.filter_skipped_paths(paths)

        cmd = [
            find_python(python_version),
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

            results = parse_to_list_of_dict(pattern, stdout)
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

        errors = settings.process_errors(results, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
