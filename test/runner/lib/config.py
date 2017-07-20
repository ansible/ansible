"""Configuration classes."""

from __future__ import absolute_import, print_function

import os
import sys

from lib.util import (
    CommonConfig,
    is_shippable,
    docker_qualify_image,
)

from lib.metadata import (
    Metadata,
)


class EnvironmentConfig(CommonConfig):
    """Configuration common to all commands which execute in an environment."""
    def __init__(self, args, command):
        """
        :type args: any
        """
        super(EnvironmentConfig, self).__init__(args)

        self.command = command

        self.local = args.local is True

        if args.tox is True or args.tox is False or args.tox is None:
            self.tox = args.tox is True
            self.tox_args = 0
            self.python = args.python if 'python' in args else None  # type: str
        else:
            self.tox = True
            self.tox_args = 1
            self.python = args.tox  # type: str

        self.docker = docker_qualify_image(args.docker)  # type: str
        self.remote = args.remote  # type: str

        self.docker_privileged = args.docker_privileged if 'docker_privileged' in args else False  # type: bool
        self.docker_util = docker_qualify_image(args.docker_util if 'docker_util' in args else '')  # type: str
        self.docker_pull = args.docker_pull if 'docker_pull' in args else False  # type: bool

        self.tox_sitepackages = args.tox_sitepackages  # type: bool

        self.remote_stage = args.remote_stage  # type: str
        self.remote_aws_region = args.remote_aws_region  # type: str
        self.remote_terminate = args.remote_terminate  # type: str

        self.requirements = args.requirements  # type: bool

        if self.python == 'default':
            self.python = '.'.join(str(i) for i in sys.version_info[:2])

        self.python_version = self.python or '.'.join(str(i) for i in sys.version_info[:2])

        self.delegate = self.tox or self.docker or self.remote

        if self.delegate:
            self.requirements = True


class TestConfig(EnvironmentConfig):
    """Configuration common to all test commands."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        super(TestConfig, self).__init__(args, command)

        self.coverage = args.coverage  # type: bool
        self.coverage_label = args.coverage_label  # type: str
        self.include = args.include  # type: list [str]
        self.exclude = args.exclude  # type: list [str]
        self.require = args.require  # type: list [str]

        self.changed = args.changed  # type: bool
        self.tracked = args.tracked  # type: bool
        self.untracked = args.untracked  # type: bool
        self.committed = args.committed  # type: bool
        self.staged = args.staged  # type: bool
        self.unstaged = args.unstaged  # type: bool
        self.changed_from = args.changed_from  # type: str
        self.changed_path = args.changed_path  # type: list [str]

        self.lint = args.lint if 'lint' in args else False  # type: bool
        self.junit = args.junit if 'junit' in args else False  # type: bool
        self.failure_ok = args.failure_ok if 'failure_ok' in args else False  # type: bool

        self.metadata = Metadata.from_file(args.metadata) if args.metadata else Metadata()
        self.metadata_path = None


class ShellConfig(EnvironmentConfig):
    """Configuration for the shell command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(ShellConfig, self).__init__(args, 'shell')


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(SanityConfig, self).__init__(args, 'sanity')

        self.test = args.test  # type: list [str]
        self.skip_test = args.skip_test  # type: list [str]
        self.list_tests = args.list_tests  # type: bool

        if args.base_branch:
            self.base_branch = args.base_branch  # str
        elif is_shippable():
            self.base_branch = os.environ.get('BASE_BRANCH', '')  # str

            if self.base_branch:
                self.base_branch = 'origin/%s' % self.base_branch
        else:
            self.base_branch = ''


class IntegrationConfig(TestConfig):
    """Configuration for the integration command."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        super(IntegrationConfig, self).__init__(args, command)

        self.start_at = args.start_at  # type: str
        self.start_at_task = args.start_at_task  # type: str
        self.allow_destructive = args.allow_destructive if 'allow_destructive' in args else False  # type: bool
        self.retry_on_error = args.retry_on_error  # type: bool
        self.continue_on_error = args.continue_on_error  # type: bool
        self.debug_strategy = args.debug_strategy  # type: bool
        self.changed_all_target = args.changed_all_target  # type: str
        self.list_targets = args.list_targets  # type: bool
        self.tags = args.tags
        self.skip_tags = args.skip_tags
        self.diff = args.diff

        if self.list_targets:
            self.explain = True


class PosixIntegrationConfig(IntegrationConfig):
    """Configuration for the posix integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(PosixIntegrationConfig, self).__init__(args, 'integration')


class WindowsIntegrationConfig(IntegrationConfig):
    """Configuration for the windows integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(WindowsIntegrationConfig, self).__init__(args, 'windows-integration')

        self.windows = args.windows  # type: list [str]

        if self.windows:
            self.allow_destructive = True


class NetworkIntegrationConfig(IntegrationConfig):
    """Configuration for the network integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(NetworkIntegrationConfig, self).__init__(args, 'network-integration')

        self.platform = args.platform  # type: list [str]
        self.inventory = args.inventory  # type: str


class UnitsConfig(TestConfig):
    """Configuration for the units command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(UnitsConfig, self).__init__(args, 'units')

        self.collect_only = args.collect_only  # type: bool


class CompileConfig(TestConfig):
    """Configuration for the compile command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CompileConfig, self).__init__(args, 'compile')


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageConfig, self).__init__(args, 'coverage')

        self.group_by = frozenset(args.group_by) if 'group_by' in args and args.group_by else set()  # type: frozenset [str]
        self.all = args.all if 'all' in args else False  # type: bool
        self.stub = args.stub if 'stub' in args else False  # type: bool


class CoverageReportConfig(CoverageConfig):
    """Configuration for the coverage report command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageReportConfig, self).__init__(args)

        self.show_missing = args.show_missing  # type: bool
