"""Scaleway plugin for integration tests."""
from __future__ import annotations

import configparser

from ....util import (
    display,
)

from ....config import (
    IntegrationConfig,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class ScalewayCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""
    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.uses_config = True

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        self._use_static_config()


class ScalewayCloudEnvironment(CloudEnvironment):
    """Updates integration test environment after delegation. Will setup the config file as parameter."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        parser = configparser.ConfigParser()
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
