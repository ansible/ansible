"""Sanity test using validate-modules."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os

from .. import types as t

from ..sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SANITY_ROOT,
)

from ..target import (
    TestTarget,
)

from ..util import (
    SubprocessError,
    display,
    find_python,
)

from ..util_common import (
    run_command,
)

from ..ansible_util import (
    ansible_environment,
)

from ..config import (
    SanityConfig,
)

from ..ci import (
    get_ci_provider,
)

from ..data import (
    data_context,
)


class ValidateModulesTest(SanitySingleVersion):
    """Sanity test using validate-modules."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'A100'

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if target.module]

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        env = ansible_environment(args, color=False)

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        cmd = [
            find_python(python_version),
            os.path.join(SANITY_ROOT, 'validate-modules', 'validate-modules'),
            '--format', 'json',
            '--arg-spec',
        ] + paths

        if data_context().content.collection:
            cmd.extend(['--collection', data_context().content.collection.directory])
        else:
            base_branch = args.base_branch or get_ci_provider().get_base_branch()

            if base_branch:
                cmd.extend([
                    '--base-branch', base_branch,
                ])
            else:
                display.warning('Cannot perform module comparison against the base branch because the base branch was not detected.')

        try:
            stdout, stderr = run_command(args, cmd, env=env, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr or status not in (0, 3):
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        messages = json.loads(stdout)

        errors = []

        for filename in messages:
            output = messages[filename]

            for item in output['errors']:
                errors.append(SanityMessage(
                    path=filename,
                    line=int(item['line']) if 'line' in item else 0,
                    column=int(item['column']) if 'column' in item else 0,
                    level='error',
                    code='%s' % item['code'],
                    message=item['msg'],
                ))

        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
