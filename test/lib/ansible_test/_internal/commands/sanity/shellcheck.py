"""Sanity test using shellcheck."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from xml.etree.ElementTree import (
    fromstring,
    Element,
)

from .. import types as t

from ..sanity import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    SANITY_ROOT,
)

from ..target import (
    TestTarget,
)

from ..util import (
    SubprocessError,
    read_lines_without_comments,
    find_executable,
)

from ..util_common import (
    run_command,
)

from ..config import (
    SanityConfig,
)


class ShellcheckTest(SanityVersionNeutral):
    """Sanity test using shellcheck."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'AT1000'

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.sh']

    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        exclude_file = os.path.join(SANITY_ROOT, 'shellcheck', 'exclude.txt')
        exclude = set(read_lines_without_comments(exclude_file, remove_blank_lines=True, optional=True))

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        if not find_executable('shellcheck', required='warning'):
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
