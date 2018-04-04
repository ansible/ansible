"""Sanity test for ansible-doc."""
from __future__ import absolute_import, print_function

import re

from lib.sanity import (
    SanityMultipleVersion,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    SanityMessage,
)

from lib.util import (
    SubprocessError,
    display,
    intercept_command,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    SanityConfig,
)


class AnsibleDocTest(SanityMultipleVersion):
    """Sanity test for ansible-doc."""
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
            skip_modules = set(skip_fd.read().splitlines())

        modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                         set(m for i in targets.exclude_external for m in i.modules) -
                         skip_modules)

        if not modules:
            return SanitySkipped(self.name, python_version=python_version)

        module_paths = dict((t.module, t.path) for t in targets.targets if t.module)

        env = ansible_environment(args, color=False)
        cmd = ['ansible-doc'] + modules

        try:
            stdout, stderr = intercept_command(args, cmd, target_name='ansible-doc', env=env, capture=True, python_version=python_version)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr:
            errors = stderr.strip().splitlines()
            messages = [self.parse_error(e, module_paths) for e in errors]

            if messages and all(messages):
                return SanityFailure(self.name, messages=messages, python_version=python_version)

        if status:
            summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
            return SanityFailure(self.name, summary=summary, python_version=python_version)

        if stdout:
            display.info(stdout.strip(), verbosity=3)

        if stderr:
            summary = u'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
            return SanityFailure(self.name, summary=summary, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)

    @staticmethod
    def parse_error(error, module_paths):
        """
        :type error: str
        :type module_paths: dict[str, str]
        :rtype: SanityMessage | None
        """
        # example error messages from lib/ansible/cli/doc.py:
        #   ERROR! module ping missing documentation (or could not parse documentation): expected string or buffer
        #   [ERROR]: module ping has a documentation error formatting or is missing documentation.
        match = re.search(r'^[^ ]*ERROR[^ ]* (?P<type>[^ ]+) (?P<name>[^ ]+) (?P<text>.*)$', error)

        if match:
            groups = match.groupdict()

            error_type = groups['type']
            error_name = groups['name']
            error_text = groups['text']

            if error_type == 'module' and error_name in module_paths:
                return SanityMessage(
                    message=error_text,
                    path=module_paths[error_name],
                )

        return None
