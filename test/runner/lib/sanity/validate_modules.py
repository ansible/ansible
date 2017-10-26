"""Sanity test using validate-modules."""
from __future__ import absolute_import, print_function

import json

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
    run_command,
    deepest_path,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    SanityConfig,
)


class ValidateModulesTest(SanitySingleVersion):
    """Sanity test using validate-modules."""
    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: SanityResult
        """
        env = ansible_environment(args, color=False)

        paths = [deepest_path(i.path, 'lib/ansible/modules/') for i in targets.include_external]
        paths = sorted(set(p for p in paths if p))

        if not paths:
            return SanitySkipped(self.name)

        cmd = [
            'python%s' % args.python_version,
            'test/sanity/validate-modules/validate-modules',
            '--format', 'json',
        ] + paths

        with open('test/sanity/validate-modules/skip.txt', 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()

        skip_paths += [e.path for e in targets.exclude_external]

        if skip_paths:
            cmd += ['--exclude', '^(%s)' % '|'.join(skip_paths)]

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

        results = []

        for filename in messages:
            output = messages[filename]

            for item in output['errors']:
                results.append(SanityMessage(
                    path=filename,
                    line=int(item['line']) if 'line' in item else 0,
                    column=int(item['column']) if 'column' in item else 0,
                    level='error',
                    code='E%s' % item['code'],
                    message=item['msg'],
                ))

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
