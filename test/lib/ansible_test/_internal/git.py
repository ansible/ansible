"""Wrapper around git command-line tools."""

from __future__ import annotations

import re
import typing as t

from .util import (
    SubprocessError,
    raw_command,
)


class Git:
    """Wrapper around git command-line tools."""

    def __init__(self, root: t.Optional[str] = None) -> None:
        self.git = 'git'
        self.root = root

    def get_diff(self, args: list[str], git_options: t.Optional[list[str]] = None) -> list[str]:
        """Run `git diff` and return the result as a list."""
        cmd = ['diff'] + args
        if git_options is None:
            git_options = ['-c', 'core.quotePath=']
        return self.run_git_split(git_options + cmd, '\n', str_errors='replace')

    def get_diff_names(self, args: list[str]) -> list[str]:
        """Return a list of file names from the `git diff` command."""
        cmd = ['diff', '--name-only', '--no-renames', '-z'] + args
        return self.run_git_split(cmd, '\0')

    def get_submodule_paths(self) -> list[str]:
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

    def get_file_names(self, args: list[str]) -> list[str]:
        """Return a list of file names from the `git ls-files` command."""
        cmd = ['ls-files', '-z'] + args
        return self.run_git_split(cmd, '\0')

    def get_branches(self) -> list[str]:
        """Return the list of branches."""
        cmd = ['for-each-ref', 'refs/heads/', '--format', '%(refname:strip=2)']
        return self.run_git_split(cmd)

    def get_branch(self) -> str:
        """Return the current branch name."""
        cmd = ['symbolic-ref', '--short', 'HEAD']
        return self.run_git(cmd).strip()

    def get_rev_list(self, commits: t.Optional[list[str]] = None, max_count: t.Optional[int] = None) -> list[str]:
        """Return the list of results from the `git rev-list` command."""
        cmd = ['rev-list']

        if commits:
            cmd += commits
        else:
            cmd += ['HEAD']

        if max_count:
            cmd += ['--max-count', '%s' % max_count]

        return self.run_git_split(cmd)

    def get_branch_fork_point(self, branch: str) -> str:
        """Return a reference to the point at which the given branch was forked."""
        cmd = ['merge-base', branch, 'HEAD']
        return self.run_git(cmd).strip()

    def is_valid_ref(self, ref: str) -> bool:
        """Return True if the given reference is valid, otherwise return False."""
        cmd = ['show', ref]
        try:
            self.run_git(cmd, str_errors='replace')
            return True
        except SubprocessError:
            return False

    def run_git_split(self, cmd: list[str], separator: t.Optional[str] = None, str_errors: str = 'strict') -> list[str]:
        """Run the given `git` command and return the results as a list."""
        output = self.run_git(cmd, str_errors=str_errors).strip(separator)

        if not output:
            return []

        return output.split(separator)

    def run_git(self, cmd: list[str], str_errors: str = 'strict') -> str:
        """Run the given `git` command and return the results as a string."""
        return raw_command([self.git] + cmd, cwd=self.root, capture=True, str_errors=str_errors)[0]
