"""Scaleway plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    ConfigParser,
    display,
)


class ScalewayCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(ScalewayCloudProvider, self).__init__(args)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        super(ScalewayCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(ScalewayCloudProvider, self).setup()

        if os.path.isfile(self.config_static_path):
            self.config_path = self.config_static_path
            self.managed = False


class ScalewayCloudEnvironment(CloudEnvironment):
    """
    Updates integration test environment after delegation. Will setup the config file as parameter.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(
            SCW_API_KEY=parser.get('default', 'key'),
            SCW_ORG=parser.get('default', 'org')
        )

        display.sensitive.add(env_vars['SCW_API_KEY'])

        ansible_vars = dict(
            scw_org=parser.get('default', 'org'),
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
