"""NS1 plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from os.path import isfile

from lib.cloud import CloudProvider, CloudEnvironment, CloudEnvironmentConfig

from lib.util import ConfigParser, display


class NS1CloudProvider(CloudProvider):
    """NS1 provider plugin. Sets up cloud resources before
       delegation.
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(NS1CloudProvider, self).__init__(args)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if isfile(self.config_static_path):
            return

        super(NS1CloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(NS1CloudProvider, self).setup()

        if isfile(self.config_static_path):
            self.config_path = self.config_static_path
            return True

        return False


class NS1CloudEnvironment(CloudEnvironment):
    """NS1 cloud environment plugin. Updates integration test environment
       after delegation.
    """

    def get_environment_config(self):
        parser = ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(NS1_TOKEN=parser.get('default', 'ns1_api_token'))

        ansible_vars = dict((key.lower(), value) for key, value in env_vars.items())

        return CloudEnvironmentConfig(env_vars=env_vars, ansible_vars=ansible_vars)
