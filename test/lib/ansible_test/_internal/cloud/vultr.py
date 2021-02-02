"""Vultr plugin for integration tests."""
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


class VultrCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""
    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VultrCloudProvider, self).__init__(args)

        self.uses_config = True

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(VultrCloudProvider, self).setup()

        if os.path.isfile(self.config_static_path):
            self.config_path = self.config_static_path
            self.managed = False


class VultrCloudEnvironment(CloudEnvironment):
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
            VULTR_API_KEY=parser.get('default', 'key'),
        )

        display.sensitive.add(env_vars['VULTR_API_KEY'])

        ansible_vars = dict(
            vultr_resource_prefix=self.resource_prefix,
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
