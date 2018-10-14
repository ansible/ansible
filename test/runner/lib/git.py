"""Wrapper around git command-line tools."""

from __future__ import absolute_import, print_function

from lib.util import (
    CommonConfig,
    SubprocessError,
    run_command,
)


class Git(object):
    """Wrapper around git command-line tools."""
    def __init__(self, args):
        """
        :type args: CommonConfig
        """
        self.args = args
        self.git = 'git'

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
        return run_command(self.args, [self.git] + cmd, capture=True, always=True, str_errors=str_errors)[0]
