"""Detect changes in Ansible code."""

from __future__ import absolute_import, print_function

import re
import os

from lib.util import (
    ApplicationError,
    SubprocessError,
    MissingEnvironmentVariable,
    CommonConfig,
    display,
)

from lib.http import (
    HttpClient,
    urlencode,
)

from lib.git import (
    Git,
)


class InvalidBranch(ApplicationError):
    """Exception for invalid branch specification."""
    def __init__(self, branch, reason):
        """
        :type branch: str
        :type reason: str
        """
        message = 'Invalid branch: %s\n%s' % (branch, reason)

        super(InvalidBranch, self).__init__(message)

        self.branch = branch


class ChangeDetectionNotSupported(ApplicationError):
    """Exception for cases where change detection is not supported."""
    pass


class ShippableChanges(object):
    """Change information for Shippable build."""
    def __init__(self, args, git):
        """
        :type args: CommonConfig
        :type git: Git
        """
        self.args = args

        try:
            self.branch = os.environ['BRANCH']
            self.is_pr = os.environ['IS_PULL_REQUEST'] == 'true'
            self.is_tag = os.environ['IS_GIT_TAG'] == 'true'
            self.commit = os.environ['COMMIT']
            self.project_id = os.environ['PROJECT_ID']
        except KeyError as ex:
            raise MissingEnvironmentVariable(name=ex.args[0])

        if self.is_tag:
            raise ChangeDetectionNotSupported('Change detection is not supported for tags.')

        if self.is_pr:
            self.paths = sorted(git.get_diff_names(['origin/%s' % self.branch, '--']))
            self.diff = git.get_diff(['origin/%s' % self.branch, '--'])
        else:
            merge_runs = self.get_merge_runs(self.project_id, self.branch)
            last_successful_commit = self.get_last_successful_commit(git, merge_runs)

            if last_successful_commit:
                self.paths = sorted(git.get_diff_names([last_successful_commit, self.commit]))
                self.diff = git.get_diff([last_successful_commit, self.commit])
            else:
                # first run for branch
                self.paths = None  # act as though change detection not enabled, do not filter targets
                self.diff = []

    def get_merge_runs(self, project_id, branch):
        """
        :type project_id: str
        :type branch: str
        :rtype: list[dict]
        """
        params = dict(
            isPullRequest='false',
            projectIds=project_id,
            branch=branch,
        )

        client = HttpClient(self.args, always=True)
        response = client.get('https://api.shippable.com/runs?%s' % urlencode(params))
        return response.json()

    @staticmethod
    def get_last_successful_commit(git, merge_runs):
        """
        :type git: Git
        :type merge_runs: dict | list[dict]
        :rtype: str
        """
        if 'id' in merge_runs and merge_runs['id'] == 4004:
            display.warning('Unable to find project. Cannot determine changes. All tests will be executed.')
            return None

        merge_runs = sorted(merge_runs, key=lambda r: r['createdAt'])
        known_commits = set()
        last_successful_commit = None

        for merge_run in merge_runs:
            commit_sha = merge_run['commitSha']
            if commit_sha not in known_commits:
                known_commits.add(commit_sha)
                if merge_run['statusCode'] == 30:
                    if git.is_valid_ref(commit_sha):
                        last_successful_commit = commit_sha

        if last_successful_commit is None:
            display.warning('No successful commit found. All tests will be executed.')

        return last_successful_commit


class LocalChanges(object):
    """Change information for local work."""
    def __init__(self, args, git):
        """
        :type args: CommonConfig
        :type git: Git
        """
        self.args = args
        self.current_branch = git.get_branch()

        if self.is_official_branch(self.current_branch):
            raise InvalidBranch(branch=self.current_branch,
                                reason='Current branch is not a feature branch.')

        self.fork_branch = None
        self.fork_point = None

        self.local_branches = sorted(git.get_branches())
        self.official_branches = sorted([b for b in self.local_branches if self.is_official_branch(b)])

        for self.fork_branch in self.official_branches:
            try:
                self.fork_point = git.get_branch_fork_point(self.fork_branch)
                break
            except SubprocessError:
                pass

        if self.fork_point is None:
            raise ApplicationError('Unable to auto-detect fork branch and fork point.')

        # tracked files (including unchanged)
        self.tracked = sorted(git.get_file_names(['--cached']))
        # untracked files (except ignored)
        self.untracked = sorted(git.get_file_names(['--others', '--exclude-standard']))
        # tracked changes (including deletions) committed since the branch was forked
        self.committed = sorted(git.get_diff_names([self.fork_point, 'HEAD']))
        # tracked changes (including deletions) which are staged
        self.staged = sorted(git.get_diff_names(['--cached']))
        # tracked changes (including deletions) which are not staged
        self.unstaged = sorted(git.get_diff_names([]))
        # diff of all tracked files from fork point to working copy
        self.diff = git.get_diff([self.fork_point])

    @staticmethod
    def is_official_branch(name):
        """
        :type name: str
        :rtype: bool
        """
        if name == 'devel':
            return True

        if re.match(r'^stable-[0-9]+\.[0-9]+$', name):
            return True

        return False
