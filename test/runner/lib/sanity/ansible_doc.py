"""Sanity test for ansible-doc."""
from __future__ import absolute_import, print_function

from lib.sanity import (
    SanityMultipleVersion,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
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
        :rtype: SanityResult
        """
        with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
            skip_modules = set(skip_fd.read().splitlines())

        modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                         set(m for i in targets.exclude_external for m in i.modules) -
                         skip_modules)

        if not modules:
            return SanitySkipped(self.name, python_version=python_version)

        env = ansible_environment(args, color=False)
        cmd = ['ansible-doc'] + modules

        try:
            stdout, stderr = intercept_command(args, cmd, target_name='ansible-doc', env=env, capture=True, python_version=python_version)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if status:
            summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
            return SanityFailure(self.name, summary=summary, python_version=python_version)

        if stdout:
            display.info(stdout.strip(), verbosity=3)

        if stderr:
            summary = u'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
            return SanityFailure(self.name, summary=summary, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)
