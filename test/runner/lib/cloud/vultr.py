"""Vultr plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment
)

from lib.util import ConfigParser


class VultrCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VultrCloudProvider, self).__init__(args, config_extension='.ini')

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        super(VultrCloudProvider, self).filter(targets, exclude)

    def setup(self):
        super(VultrCloudProvider, self).setup()

        if os.path.isfile(self.config_static_path):
            self.config_path = self.config_static_path
            self.managed = False
            return True
        return False


class VultrCloudEnvironment(CloudEnvironment):
    """
    Updates integration test environment after delegation. Will setup the config file as parameter.
    """

    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        changes = dict(
            VULTR_API_KEY=parser.get('default', 'key'),
        )
        env.update(changes)

        cmd.append('-e')
        cmd.append('vultr_resource_prefix=%s' % self.resource_prefix)
