"""Configuration classes."""

from __future__ import absolute_import, print_function

import os

from lib.util import (
    EnvironmentConfig,
    is_shippable,
)

from lib.test import (
    TestConfig,
)


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
        self.tags = args.tags
        self.skip_tags = args.skip_tags
        self.diff = args.diff


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

        self.platform = args.platform  # type list [str]


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
