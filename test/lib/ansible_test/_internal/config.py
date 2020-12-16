"""Configuration classes."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from . import types as t

from .util import (
    docker_qualify_image,
    find_python,
    generate_pip_command,
    get_docker_completion,
    ApplicationError,
)

from .util_common import (
    CommonConfig,
)

from .metadata import (
    Metadata,
)

from .data import (
    data_context,
)

try:
    TIntegrationConfig = t.TypeVar('TIntegrationConfig', bound='IntegrationConfig')
except AttributeError:
    TIntegrationConfig = None  # pylint: disable=invalid-name


class EnvironmentConfig(CommonConfig):
    """Configuration common to all commands which execute in an environment."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        super(EnvironmentConfig, self).__init__(args, command)

        self.local = args.local is True
        self.venv = args.venv
        self.venv_system_site_packages = args.venv_system_site_packages

        if args.tox is True or args.tox is False or args.tox is None:
            self.tox = args.tox is True
            self.tox_args = 0
            self.python = args.python if 'python' in args else None  # type: str
        else:
            self.tox = True
            self.tox_args = 1
            self.python = args.tox  # type: str

        self.docker = docker_qualify_image(args.docker)  # type: str
        self.docker_raw = args.docker  # type: str
        self.remote = args.remote  # type: str

        self.docker_privileged = args.docker_privileged if 'docker_privileged' in args else False  # type: bool
        self.docker_pull = args.docker_pull if 'docker_pull' in args else False  # type: bool
        self.docker_keep_git = args.docker_keep_git if 'docker_keep_git' in args else False  # type: bool
        self.docker_seccomp = args.docker_seccomp if 'docker_seccomp' in args else None  # type: str
        self.docker_memory = args.docker_memory if 'docker_memory' in args else None
        self.docker_network = args.docker_network if 'docker_network' in args else None  # type: str

        if self.docker_seccomp is None:
            self.docker_seccomp = get_docker_completion().get(self.docker_raw, {}).get('seccomp', 'default')

        self.tox_sitepackages = args.tox_sitepackages  # type: bool

        self.remote_stage = args.remote_stage  # type: str
        self.remote_provider = args.remote_provider  # type: str
        self.remote_endpoint = args.remote_endpoint  # type: t.Optional[str]
        self.remote_aws_region = args.remote_aws_region  # type: str
        self.remote_terminate = args.remote_terminate  # type: str

        if self.remote_provider == 'default':
            self.remote_provider = None

        self.requirements = args.requirements  # type: bool

        if self.python == 'default':
            self.python = None

        actual_major_minor = '.'.join(str(i) for i in sys.version_info[:2])

        self.python_version = self.python or actual_major_minor
        self.python_interpreter = args.python_interpreter

        self.delegate = self.tox or self.docker or self.remote or self.venv
        self.delegate_args = []  # type: t.List[str]

        if self.delegate:
            self.requirements = True

        self.inject_httptester = args.inject_httptester if 'inject_httptester' in args else False  # type: bool
        self.httptester = docker_qualify_image(args.httptester if 'httptester' in args else '')  # type: str

        if args.check_python and args.check_python != actual_major_minor:
            raise ApplicationError('Running under Python %s instead of Python %s as expected.' % (actual_major_minor, args.check_python))

        if self.docker_keep_git:
            def git_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
                """Add files from the content root .git directory to the payload file list."""
                for dirpath, _dirnames, filenames in os.walk(os.path.join(data_context().content.root, '.git')):
                    paths = [os.path.join(dirpath, filename) for filename in filenames]
                    files.extend((path, os.path.relpath(path, data_context().content.root)) for path in paths)

            data_context().register_payload_callback(git_callback)

    @property
    def python_executable(self):
        """
        :rtype: str
        """
        return find_python(self.python_version)

    @property
    def pip_command(self):
        """
        :rtype: list[str]
        """
        return generate_pip_command(self.python_executable)


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
        self.coverage_check = args.coverage_check  # type: bool
        self.coverage_config_base_path = None  # type: t.Optional[str]
        self.include = args.include or []  # type: t.List[str]
        self.exclude = args.exclude or []  # type: t.List[str]
        self.require = args.require or []  # type: t.List[str]

        self.changed = args.changed  # type: bool
        self.tracked = args.tracked  # type: bool
        self.untracked = args.untracked  # type: bool
        self.committed = args.committed  # type: bool
        self.staged = args.staged  # type: bool
        self.unstaged = args.unstaged  # type: bool
        self.changed_from = args.changed_from  # type: str
        self.changed_path = args.changed_path  # type: t.List[str]
        self.base_branch = args.base_branch  # type: str

        self.lint = args.lint if 'lint' in args else False  # type: bool
        self.junit = args.junit if 'junit' in args else False  # type: bool
        self.failure_ok = args.failure_ok if 'failure_ok' in args else False  # type: bool

        self.metadata = Metadata.from_file(args.metadata) if args.metadata else Metadata()
        self.metadata_path = None

        if self.coverage_check:
            self.coverage = True

        def metadata_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """Add the metadata file to the payload file list."""
            config = self

            if data_context().content.collection:
                working_path = data_context().content.collection.directory
            else:
                working_path = ''

            if self.metadata_path:
                files.append((os.path.abspath(config.metadata_path), os.path.join(working_path, config.metadata_path)))

        data_context().register_payload_callback(metadata_callback)


class ShellConfig(EnvironmentConfig):
    """Configuration for the shell command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(ShellConfig, self).__init__(args, 'shell')

        self.raw = args.raw  # type: bool

        if self.raw:
            self.httptester = False


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(SanityConfig, self).__init__(args, 'sanity')

        self.test = args.test  # type: t.List[str]
        self.skip_test = args.skip_test  # type: t.List[str]
        self.list_tests = args.list_tests  # type: bool
        self.allow_disabled = args.allow_disabled  # type: bool


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
        self.allow_destructive = args.allow_destructive  # type: bool
        self.allow_root = args.allow_root  # type: bool
        self.allow_disabled = args.allow_disabled  # type: bool
        self.allow_unstable = args.allow_unstable  # type: bool
        self.allow_unstable_changed = args.allow_unstable_changed  # type: bool
        self.allow_unsupported = args.allow_unsupported  # type: bool
        self.retry_on_error = args.retry_on_error  # type: bool
        self.continue_on_error = args.continue_on_error  # type: bool
        self.debug_strategy = args.debug_strategy  # type: bool
        self.changed_all_target = args.changed_all_target  # type: str
        self.changed_all_mode = args.changed_all_mode  # type: str
        self.list_targets = args.list_targets  # type: bool
        self.tags = args.tags
        self.skip_tags = args.skip_tags
        self.diff = args.diff
        self.no_temp_workdir = args.no_temp_workdir
        self.no_temp_unicode = args.no_temp_unicode

        if self.list_targets:
            self.explain = True

    def get_ansible_config(self):  # type: () -> str
        """Return the path to the Ansible config for the given config."""
        ansible_config_relative_path = os.path.join(data_context().content.integration_path, '%s.cfg' % self.command)
        ansible_config_path = os.path.join(data_context().content.root, ansible_config_relative_path)

        if not os.path.exists(ansible_config_path):
            # use the default empty configuration unless one has been provided
            ansible_config_path = super(IntegrationConfig, self).get_ansible_config()

        return ansible_config_path


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

        self.windows = args.windows  # type: t.List[str]
        self.inventory = args.inventory  # type: str

        if self.windows:
            self.allow_destructive = True


class NetworkIntegrationConfig(IntegrationConfig):
    """Configuration for the network integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(NetworkIntegrationConfig, self).__init__(args, 'network-integration')

        self.platform = args.platform  # type: t.List[str]
        self.inventory = args.inventory  # type: str
        self.testcase = args.testcase  # type: str


class UnitsConfig(TestConfig):
    """Configuration for the units command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(UnitsConfig, self).__init__(args, 'units')

        self.collect_only = args.collect_only  # type: bool
        self.num_workers = args.num_workers  # type: int

        self.requirements_mode = args.requirements_mode if 'requirements_mode' in args else ''

        if self.requirements_mode == 'only':
            self.requirements = True
        elif self.requirements_mode == 'skip':
            self.requirements = False


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageConfig, self).__init__(args, 'coverage')

        self.group_by = frozenset(args.group_by) if 'group_by' in args and args.group_by else set()  # type: t.FrozenSet[str]
        self.all = args.all if 'all' in args else False  # type: bool
        self.stub = args.stub if 'stub' in args else False  # type: bool
        self.export = args.export if 'export' in args else None  # type: str
        self.coverage = False  # temporary work-around to support intercept_command in cover.py


class CoverageReportConfig(CoverageConfig):
    """Configuration for the coverage report command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageReportConfig, self).__init__(args)

        self.show_missing = args.show_missing  # type: bool
        self.include = args.include  # type: str
        self.omit = args.omit  # type: str
