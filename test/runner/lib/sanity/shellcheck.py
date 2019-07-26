"""Sanity test using shellcheck."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from xml.etree.ElementTree import (
    fromstring,
    Element,
)

import lib.types as t

from lib.sanity import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
)

from lib.util import (
    SubprocessError,
    read_lines_without_comments,
    ANSIBLE_ROOT,
)

from lib.util_common import (
    run_command,
)

from lib.config import (
    SanityConfig,
)


class ShellcheckTest(SanityVersionNeutral):
    """Sanity test using shellcheck."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'AT1000'

    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        exclude_file = os.path.join(ANSIBLE_ROOT, 'test/sanity/shellcheck/exclude.txt')
        exclude = set(read_lines_without_comments(exclude_file, remove_blank_lines=True, optional=True))

        settings = self.load_processor(args)

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh')
        paths = settings.filter_skipped_paths(paths)

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            'shellcheck',
            '-e', ','.join(sorted(exclude)),
            '--format', 'checkstyle',
        ] + paths

        try:
            stdout, stderr = run_command(args, cmd, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr or status > 1:
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        # json output is missing file paths in older versions of shellcheck, so we'll use xml instead
        root = fromstring(stdout)  # type: Element

        results = []

        for item in root:  # type: Element
            for entry in item:  # type: Element
                results.append(SanityMessage(
                    message=entry.attrib['message'],
                    path=item.attrib['name'],
                    line=int(entry.attrib['line']),
                    column=int(entry.attrib['column']),
                    level=entry.attrib['severity'],
                    code=entry.attrib['source'].replace('ShellCheck.', ''),
                ))

        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
