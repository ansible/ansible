"""Plugin system for cloud providers and environments for use in integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import atexit
import datetime
import time
import os
import re
import tempfile

from .. import types as t

from ..encoding import (
    to_bytes,
)

from ..io import (
    read_text_file,
)

from ..util import (
    ApplicationError,
    display,
    import_plugins,
    load_plugins,
    ABC,
    ANSIBLE_TEST_CONFIG_ROOT,
)

from ..util_common import (
    write_json_test_results,
    ResultType,
)

from ..target import (
    TestTarget,
)

from ..config import (
    IntegrationConfig,
)

from ..ci import (
    get_ci_provider,
)

from ..data import (
    data_context,
)

PROVIDERS = {}
ENVIRONMENTS = {}


def initialize_cloud_plugins():
    """Import cloud plugins and load them into the plugin dictionaries."""
    import_plugins('cloud')

    load_plugins(CloudProvider, PROVIDERS)
    load_plugins(CloudEnvironment, ENVIRONMENTS)


def get_cloud_platforms(args, targets=None):
    """
    :type args: TestConfig
    :type targets: tuple[IntegrationTarget] | None
    :rtype: list[str]
    """
    if isinstance(args, IntegrationConfig):
        if args.list_targets:
            return []

    if targets is None:
        cloud_platforms = set(args.metadata.cloud_config or [])
    else:
        cloud_platforms = set(get_cloud_platform(target) for target in targets)

    cloud_platforms.discard(None)

    return sorted(cloud_platforms)


def get_cloud_platform(target):
    """
    :type target: IntegrationTarget
    :rtype: str | None
    """
    cloud_platforms = set(a.split('/')[1] for a in target.aliases if a.startswith('cloud/') and a.endswith('/') and a != 'cloud/')

    if not cloud_platforms:
        return None

    if len(cloud_platforms) == 1:
        cloud_platform = cloud_platforms.pop()

        if cloud_platform not in PROVIDERS:
            raise ApplicationError('Target %s aliases contains unknown cloud platform: %s' % (target.name, cloud_platform))

        return cloud_platform

    raise ApplicationError('Target %s aliases contains multiple cloud platforms: %s' % (target.name, ', '.join(sorted(cloud_platforms))))


def get_cloud_providers(args, targets=None):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget] | None
    :rtype: list[CloudProvider]
    """
    return [PROVIDERS[p](args) for p in get_cloud_platforms(args, targets)]


def get_cloud_environment(args, target):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :rtype: CloudEnvironment
    """
    cloud_platform = get_cloud_platform(target)

    if not cloud_platform:
        return None

    return ENVIRONMENTS[cloud_platform](args)


def cloud_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :return: list[str]
    """
    if args.metadata.cloud_config is not None:
        return []  # cloud filter already performed prior to delegation

    exclude = []

    for provider in get_cloud_providers(args, targets):
        provider.filter(targets, exclude)

    return exclude


def cloud_init(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    """
    if args.metadata.cloud_config is not None:
        return  # cloud configuration already established prior to delegation

    args.metadata.cloud_config = {}

    results = {}

    for provider in get_cloud_providers(args, targets):
        args.metadata.cloud_config[provider.platform] = {}

        start_time = time.time()
        provider.setup()
        end_time = time.time()

        results[provider.platform] = dict(
            platform=provider.platform,
            setup_seconds=int(end_time - start_time),
            targets=[target.name for target in targets],
        )

    if not args.explain and results:
        result_name = '%s-%s.json' % (
            args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.utcnow().replace(microsecond=0))))

        data = dict(
            clouds=results,
        )

        write_json_test_results(ResultType.DATA, result_name, data)


class CloudBase(ABC):
    """Base class for cloud plugins."""
    __metaclass__ = abc.ABCMeta

    _CONFIG_PATH = 'config_path'
    _RESOURCE_PREFIX = 'resource_prefix'
    _MANAGED = 'managed'
    _SETUP_EXECUTED = 'setup_executed'

    def __init__(self, args):
        """
        :type args: IntegrationConfig
        """
        self.args = args
        self.platform = self.__module__.split('.')[-1]

        def config_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """Add the config file to the payload file list."""
            if self._get_cloud_config(self._CONFIG_PATH, ''):
                pair = (self.config_path, os.path.relpath(self.config_path, data_context().content.root))

                if pair not in files:
                    display.info('Including %s config: %s -> %s' % (self.platform, pair[0], pair[1]), verbosity=3)
                    files.append(pair)

        data_context().register_payload_callback(config_callback)

    @property
    def setup_executed(self):
        """
        :rtype: bool
        """
        return self._get_cloud_config(self._SETUP_EXECUTED, False)

    @setup_executed.setter
    def setup_executed(self, value):
        """
        :type value: bool
        """
        self._set_cloud_config(self._SETUP_EXECUTED, value)

    @property
    def config_path(self):
        """
        :rtype: str
        """
        return os.path.join(data_context().content.root, self._get_cloud_config(self._CONFIG_PATH))

    @config_path.setter
    def config_path(self, value):
        """
        :type value: str
        """
        self._set_cloud_config(self._CONFIG_PATH, value)

    @property
    def resource_prefix(self):
        """
        :rtype: str
        """
        return self._get_cloud_config(self._RESOURCE_PREFIX)

    @resource_prefix.setter
    def resource_prefix(self, value):
        """
        :type value: str
        """
        self._set_cloud_config(self._RESOURCE_PREFIX, value)

    @property
    def managed(self):
        """
        :rtype: bool
        """
        return self._get_cloud_config(self._MANAGED)

    @managed.setter
    def managed(self, value):
        """
        :type value: bool
        """
        self._set_cloud_config(self._MANAGED, value)

    def _get_cloud_config(self, key, default=None):
        """
        :type key: str
        :type default: str | int | bool | None
        :rtype: str | int | bool
        """
        if default is not None:
            return self.args.metadata.cloud_config[self.platform].get(key, default)

        return self.args.metadata.cloud_config[self.platform][key]

    def _set_cloud_config(self, key, value):
        """
        :type key: str
        :type value: str | int | bool
        """
        self.args.metadata.cloud_config[self.platform][key] = value


class CloudProvider(CloudBase):
    """Base class for cloud provider plugins. Sets up cloud resources before delegation."""
    def __init__(self, args, config_extension='.ini'):
        """
        :type args: IntegrationConfig
        :type config_extension: str
        """
        super(CloudProvider, self).__init__(args)

        self.ci_provider = get_ci_provider()
        self.remove_config = False
        self.config_static_name = 'cloud-config-%s%s' % (self.platform, config_extension)
        self.config_static_path = os.path.join(data_context().content.integration_path, self.config_static_name)
        self.config_template_path = os.path.join(ANSIBLE_TEST_CONFIG_ROOT, '%s.template' % self.config_static_name)
        self.config_extension = config_extension

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require config (see "%s"): %s'
                            % (skip.rstrip('/'), self.config_template_path, ', '.join(skipped)))

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        self.resource_prefix = self.ci_provider.generate_resource_prefix()
        self.resource_prefix = re.sub(r'[^a-zA-Z0-9]+', '-', self.resource_prefix)[:63].lower().rstrip('-')

        atexit.register(self.cleanup)

    def get_remote_ssh_options(self):
        """Get any additional options needed when delegating tests to a remote instance via SSH.
        :rtype: list[str]
        """
        return []

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker container.
        :rtype: list[str]
        """
        return []

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.remove_config:
            os.remove(self.config_path)

    def _use_static_config(self):
        """
        :rtype: bool
        """
        if os.path.isfile(self.config_static_path):
            display.info('Using existing %s cloud config: %s' % (self.platform, self.config_static_path), verbosity=1)
            self.config_path = self.config_static_path
            static = True
        else:
            static = False

        self.managed = not static

        return static

    def _write_config(self, content):
        """
        :type content: str
        """
        prefix = '%s-' % os.path.splitext(os.path.basename(self.config_static_path))[0]

        with tempfile.NamedTemporaryFile(dir=data_context().content.integration_path, prefix=prefix, suffix=self.config_extension, delete=False) as config_fd:
            filename = os.path.join(data_context().content.integration_path, os.path.basename(config_fd.name))

            self.config_path = filename
            self.remove_config = True

            display.info('>>> Config: %s\n%s' % (filename, content.strip()), verbosity=3)

            config_fd.write(to_bytes(content))
            config_fd.flush()

    def _read_config_template(self):
        """
        :rtype: str
        """
        lines = read_text_file(self.config_template_path).splitlines()
        lines = [line for line in lines if not line.startswith('#')]
        config = '\n'.join(lines).strip() + '\n'
        return config

    @staticmethod
    def _populate_config_template(template, values):
        """
        :type template: str
        :type values: dict[str, str]
        :rtype: str
        """
        for key in sorted(values):
            value = values[key]
            template = template.replace('@%s' % key, value)

        return template


class CloudEnvironment(CloudBase):
    """Base class for cloud environment plugins. Updates integration test environment after delegation."""
    def setup_once(self):
        """Run setup if it has not already been run."""
        if self.setup_executed:
            return

        self.setup()
        self.setup_executed = True

    def setup(self):
        """Setup which should be done once per environment instead of once per test target."""

    @abc.abstractmethod
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """

    def on_failure(self, target, tries):
        """
        :type target: IntegrationTarget
        :type tries: int
        """


class CloudEnvironmentConfig:
    """Configuration for the environment."""
    def __init__(self, env_vars=None, ansible_vars=None, module_defaults=None, callback_plugins=None):
        """
        :type env_vars: dict[str, str] | None
        :type ansible_vars: dict[str, any] | None
        :type module_defaults: dict[str, dict[str, any]] | None
        :type callback_plugins: list[str] | None
        """
        self.env_vars = env_vars
        self.ansible_vars = ansible_vars
        self.module_defaults = module_defaults
        self.callback_plugins = callback_plugins
