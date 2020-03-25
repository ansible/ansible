"""Wrapper around git command-line tools."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from . import types as t

from .util import (
    SubprocessError,
    raw_command,
)


class Git:
    """Wrapper around git command-line tools."""
    def __init__(self, root=None):  # type: (t.Optional[str]) -> None
        self.git = 'git'
        self.root = root

    def get_diff(self, args, git_options=None):
        """
        :type args: list[str]
        :type git_options: list[str] | None
        :rtype: list[str]
        """
        cmd = ['diff'] + args
        if git_options is None:
            git_options = ['-c', 'core.quotePath=']
        return self.run_git_split(git_options + cmd, '\n', str_errors='replace')

    def get_diff_names(self, args):
        """
        :type args: list[str]
        :rtype: list[str]
        """
        cmd = ['diff', '--name-only', '--no-renames', '-z'] + args
        return self.run_git_split(cmd, '\0')

    def get_submodule_paths(self):  # type: () -> t.List[str]
        """Return a list of submodule paths recursively."""
        cmd = ['submodule', 'status', '--recursive']
        output = self.run_git_split(cmd, '\n')
        submodule_paths = [re.search(r'^.[0-9a-f]+ (?P<path>[^ ]+)', line).group('path') for line in output]

        # status is returned for all submodules in the current git repository relative to the current directory
        # when the current directory is not the root of the git repository this can yield relative paths which are not below the current directory
        # this can occur when multiple collections are in a git repo and some collections are submodules when others are not
        # specifying "." as the path to enumerate would limit results to the current directory, but can cause the git command to fail with the error:
        #   error: pathspec '.' did not match any file(s) known to git
        # this can occur when the current directory contains no files tracked by git
        # instead we'll filter out the relative paths, since we're only interested in those at or below the current directory
        submodule_paths = [path for path in submodule_paths if not path.startswith('../')]

        return submodule_paths

    def get_file_names(self, args):
        """
        :type args: list[str]
        :rtype: list[str]
        """
        cmd = ['ls-files', '-z'] + args
        return self.run_git_split(cmd, '\0')

    def get_branches(self):
        """
        :rtype: list[str]
        """
        cmd = ['for-each-ref', 'refs/heads/', '--format', '%(refname:strip=2)']
        return self.run_git_split(cmd)

    def get_branch(self):
        """
        :rtype: str
        """
        cmd = ['symbolic-ref', '--short', 'HEAD']
        return self.run_git(cmd).strip()

    def get_rev_list(self, commits=None, max_count=None):
        """
        :type commits: list[str] | None
        :type max_count: int | None
        :rtype: list[str]
        """
        cmd = ['rev-list']

        if commits:
            cmd += commits
        else:
            cmd += ['HEAD']

        if max_count:
            cmd += ['--max-count', '%s' % max_count]

        return self.run_git_split(cmd)

    def get_branch_fork_point(self, branch):
        """
        :type branch: str
        :rtype: str
        """
        cmd = ['merge-base', '--fork-point', branch]
        return self.run_git(cmd).strip()

    def is_valid_ref(self, ref):
        """
        :type ref: str
        :rtype: bool
        """
        cmd = ['show', ref]
        try:
            self.run_git(cmd, str_errors='replace')
            return True
        except SubprocessError:
            return False

    def run_git_split(self, cmd, separator=None, str_errors='strict'):
        """
        :type cmd: list[str]
        :type separator: str | None
        :type str_errors: str
        :rtype: list[str]
        """
        output = self.run_git(cmd, str_errors=str_errors).strip(separator)

        if not output:
            return []

        return output.split(separator)

    def run_git(self, cmd, str_errors='strict'):
        """
        :type cmd: list[str]
        :type str_errors: str
        :rtype: str
        """
        return raw_command([self.git] + cmd, cwd=self.root, capture=True, str_errors=str_errors)[0]
