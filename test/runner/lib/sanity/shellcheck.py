"""Sanity test using shellcheck."""
from __future__ import absolute_import, print_function

import os

from xml.etree.ElementTree import (
    fromstring,
    Element,
)

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
)

from lib.config import (
    SanityConfig,
)


class ShellcheckTest(SanitySingleVersion):
    """Sanity test using shellcheck."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        with open('test/sanity/shellcheck/skip.txt', 'r') as skip_fd:
            skip_paths = set(skip_fd.read().splitlines())

        with open('test/sanity/shellcheck/exclude.txt', 'r') as exclude_fd:
            exclude = set(exclude_fd.read().splitlines())

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh' and i.path not in skip_paths)

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

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
