"""Hetzner Cloud plugin for integration tests."""
from __future__ import absolute_import, print_function

from os.path import isfile

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from lib.util import ConfigParser, display


class HcloudCloudProvider(CloudProvider):
    """Hetzner Cloud provider plugin. Sets up cloud resources before
       delegation.
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(HcloudCloudProvider, self).__init__(args)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if isfile(self.config_static_path):
            return

        super(HcloudCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(HcloudCloudProvider, self).setup()

        if isfile(self.config_static_path):
            self.config_path = self.config_static_path
            return True

        return False


class HcloudCloudEnvironment(CloudEnvironment):
    """Hetzner Cloud cloud environment plugin. Updates integration test environment
       after delegation.
    """

    def get_environment_config(self):
        parser = ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(
            HCLOUD_TOKEN=parser.get('default', 'hcloud_api_token'),
        )

        ansible_vars = dict(
            hcloud_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict((key.lower(), value) for key, value in env_vars.items()))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
