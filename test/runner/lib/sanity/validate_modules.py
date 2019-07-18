"""Sanity test using validate-modules."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
    display,
    ANSIBLE_ROOT,
)

from lib.util_common import (
    run_command,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    SanityConfig,
)

from lib.data import (
    data_context,
)

UNSUPPORTED_PYTHON_VERSIONS = (
    '2.6',
    '2.7',
)


class ValidateModulesTest(SanitySingleVersion):
    """Sanity test using validate-modules."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        if args.python_version in UNSUPPORTED_PYTHON_VERSIONS:
            display.warning('Skipping validate-modules on unsupported Python version %s.' % args.python_version)
            return SanitySkipped(self.name)

        if data_context().content.is_ansible:
            ignore_codes = ()
        else:
            ignore_codes = ((
                'E502',  # only ansible content requires __init__.py for module subdirectories
            ))

        env = ansible_environment(args, color=False)

        settings = self.load_settings(args, 'A100')

        paths = sorted(i.path for i in targets.include if i.module)
        paths = settings.filter_skipped_paths(paths)

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            args.python_executable,
            os.path.join(ANSIBLE_ROOT, 'test/sanity/validate-modules/validate-modules'),
            '--format', 'json',
            '--arg-spec',
        ] + paths

        if args.base_branch:
            cmd.extend([
                '--base-branch', args.base_branch,
            ])
        else:
            display.warning('Cannot perform module comparison against the base branch. Base branch not detected when running locally.')

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
                    code='E%s' % item['code'],
                    message=item['msg'],
                ))

        errors = [error for error in errors if error.code not in ignore_codes]
        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
