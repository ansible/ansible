"""Gandi plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from lib.util import ConfigParser


class GandiCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(GandiCloudProvider, self).__init__(args)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        super(GandiCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(GandiCloudProvider, self).setup()

        if os.path.isfile(self.config_static_path):
            self.config_path = self.config_static_path
            self.managed = False


class GandiCloudEnvironment(CloudEnvironment):
    """
    Updates integration test environment after delegation. Will setup the config file as parameter.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        ansible_vars = dict(
            gandi_api_key=parser.get('default', 'gandi_api_key'),
        )

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
