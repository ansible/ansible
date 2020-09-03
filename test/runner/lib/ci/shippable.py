"""Support code for working with Shippable."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import time

from .. import types as t

from ..config import (
    CommonConfig,
    TestConfig,
)

from ..git import (
    Git,
)

from ..http import (
    HttpClient,
    urlencode,
)

from ..util import (
    ApplicationError,
    display,
    MissingEnvironmentVariable,
    SubprocessError,
)

from . import (
    AuthContext,
    ChangeDetectionNotSupported,
    CIProvider,
    OpenSSLAuthHelper,
)


CODE = 'shippable'


class Shippable(CIProvider):
    """CI provider implementation for Shippable."""
    def __init__(self):
        self.auth = ShippableAuthHelper()

    @staticmethod
    def is_supported():  # type: () -> bool
        """Return True if this provider is supported in the current running environment."""
        return os.environ.get('SHIPPABLE') == 'true'

    @property
    def code(self):  # type: () -> str
        """Return a unique code representing this provider."""
        return CODE

    @property
    def name(self):  # type: () -> str
        """Return descriptive name for this provider."""
        return 'Shippable'

    def generate_resource_prefix(self):  # type: () -> str
        """Return a resource prefix specific to this CI provider."""
        try:
            prefix = 'shippable-%s-%s' % (
                os.environ['SHIPPABLE_BUILD_NUMBER'],
                os.environ['SHIPPABLE_JOB_NUMBER'],
            )
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0])

        return prefix

    def get_base_branch(self):  # type: () -> str
        """Return the base branch or an empty string."""
        base_branch = os.environ.get('BASE_BRANCH')

        if base_branch:
            base_branch = 'origin/%s' % base_branch

        return base_branch or ''

    def detect_changes(self, args):  # type: (TestConfig) -> t.Optional[t.List[str]]
        """Initialize change detection."""
        result = ShippableChanges(args)

        if result.is_pr:
            job_type = 'pull request'
        elif result.is_tag:
            job_type = 'tag'
        else:
            job_type = 'merge commit'

        display.info('Processing %s for branch %s commit %s' % (job_type, result.branch, result.commit))

        if not args.metadata.changes:
            args.metadata.populate_changes(result.diff)

        if result.paths is None:
            # There are several likely causes of this:
            # - First run on a new branch.
            # - Too many pull requests passed since the last merge run passed.
            display.warning('No successful commit found. All tests will be executed.')

        return result.paths

    def supports_core_ci_auth(self, context):  # type: (AuthContext) -> bool
        """Return True if Ansible Core CI is supported."""
        return True

    def prepare_core_ci_auth(self, context):  # type: (AuthContext) -> t.Dict[str, t.Any]
        """Return authentication details for Ansible Core CI."""
        try:
            request = dict(
                run_id=os.environ['SHIPPABLE_BUILD_ID'],
                job_number=int(os.environ['SHIPPABLE_JOB_NUMBER']),
            )
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0])

        self.auth.sign_request(request)

        auth = dict(
            shippable=request,
        )

        return auth

    def get_git_details(self, args):  # type: (CommonConfig) -> t.Optional[t.Dict[str, t.Any]]
        """Return details about git in the current environment."""
        commit = os.environ.get('COMMIT')
        base_commit = os.environ.get('BASE_COMMIT')

        details = dict(
            base_commit=base_commit,
            commit=commit,
            merged_commit=self._get_merged_commit(args, commit),
        )

        return details

    # noinspection PyUnusedLocal
    def _get_merged_commit(self, args, commit):  # type: (CommonConfig, str) -> t.Optional[str]  # pylint: disable=unused-argument
        """Find the merged commit that should be present."""
        if not commit:
            return None

        git = Git(args)

        try:
            show_commit = git.run_git(['show', '--no-patch', '--no-abbrev', commit])
        except SubprocessError as ex:
            # This should only fail for pull requests where the commit does not exist.
            # Merge runs would fail much earlier when attempting to checkout the commit.
            raise ApplicationError('Commit %s was not found:\n\n%s\n\n'
                                   'GitHub may not have fully replicated the commit across their infrastructure.\n'
                                   'It is also possible the commit was removed by a force push between job creation and execution.\n'
                                   'Find the latest run for the pull request and restart failed jobs as needed.'
                                   % (commit, ex.stderr.strip()))

        head_commit = git.run_git(['show', '--no-patch', '--no-abbrev', 'HEAD'])

        if show_commit == head_commit:
            # Commit is HEAD, so this is not a pull request or the base branch for the pull request is up-to-date.
            return None

        match_merge = re.search(r'^Merge: (?P<parents>[0-9a-f]{40} [0-9a-f]{40})$', head_commit, flags=re.MULTILINE)

        if not match_merge:
            # The most likely scenarios resulting in a failure here are:
            # A new run should or does supersede this job, but it wasn't cancelled in time.
            # A job was superseded and then later restarted.
            raise ApplicationError('HEAD is not commit %s or a merge commit:\n\n%s\n\n'
                                   'This job has likely been superseded by another run due to additional commits being pushed.\n'
                                   'Find the latest run for the pull request and restart failed jobs as needed.'
                                   % (commit, head_commit.strip()))

        parents = set(match_merge.group('parents').split(' '))

        if len(parents) != 2:
            raise ApplicationError('HEAD is a %d-way octopus merge.' % len(parents))

        if commit not in parents:
            raise ApplicationError('Commit %s is not a parent of HEAD.' % commit)

        parents.remove(commit)

        last_commit = parents.pop()

        return last_commit


class ShippableAuthHelper(OpenSSLAuthHelper):
    """
    Authentication helper for Shippable.
    Based on OpenSSL since cryptography is not provided by the default Shippable environment.
    """
    def publish_public_key(self, public_key_pem):  # type: (str) -> None
        """Publish the given public key."""
        # display the public key as a single line to avoid mangling such as when prefixing each line with a timestamp
        display.info(public_key_pem.replace('\n', ' '))
        # allow time for logs to become available to reduce repeated API calls
        time.sleep(3)


class ShippableChanges:
    """Change information for Shippable build."""
    def __init__(self, args):  # type: (CommonConfig) -> None
        self.args = args
        self.git = Git(args)

        try:
            self.branch = os.environ['BRANCH']
            self.is_pr = os.environ['IS_PULL_REQUEST'] == 'true'
            self.is_tag = os.environ['IS_GIT_TAG'] == 'true'
            self.commit = os.environ['COMMIT']
            self.project_id = os.environ['PROJECT_ID']
            self.commit_range = os.environ['SHIPPABLE_COMMIT_RANGE']
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0])

        if self.is_tag:
            raise ChangeDetectionNotSupported('Change detection is not supported for tags.')

        if self.is_pr:
            self.paths = sorted(self.git.get_diff_names([self.commit_range]))
            self.diff = self.git.get_diff([self.commit_range])
        else:
            commits = self.get_successful_merge_run_commits(self.project_id, self.branch)
            last_successful_commit = self.get_last_successful_commit(commits)

            if last_successful_commit:
                self.paths = sorted(self.git.get_diff_names([last_successful_commit, self.commit]))
                self.diff = self.git.get_diff([last_successful_commit, self.commit])
            else:
                # first run for branch
                self.paths = None  # act as though change detection not enabled, do not filter targets
                self.diff = []

    def get_successful_merge_run_commits(self, project_id, branch):  # type: (str, str) -> t.Set[str]
        """Return a set of recent successsful merge commits from Shippable for the given project and branch."""
        parameters = dict(
            isPullRequest='false',
            projectIds=project_id,
            branch=branch,
        )

        url = 'https://api.shippable.com/runs?%s' % urlencode(parameters)

        http = HttpClient(self.args, always=True)
        response = http.get(url)
        result = response.json()

        if 'id' in result and result['id'] == 4004:
            # most likely due to a private project, which returns an HTTP 200 response with JSON
            display.warning('Unable to find project. Cannot determine changes. All tests will be executed.')
            return set()

        commits = set(run['commitSha'] for run in result if run['statusCode'] == 30)

        return commits

    def get_last_successful_commit(self, successful_commits):  # type: (t.Set[str]) -> t.Optional[str]
        """Return the last successful commit from git history that is found in the given commit list, or None."""
        commit_history = self.git.get_rev_list(max_count=100)
        ordered_successful_commits = [commit for commit in commit_history if commit in successful_commits]
        last_successful_commit = ordered_successful_commits[0] if ordered_successful_commits else None
        return last_successful_commit
