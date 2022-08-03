# -*- coding: utf-8 -*-
#
# (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Cloudscale plugin for integration tests."""
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


class CloudscaleCloudProvider(CloudProvider):
    """Cloudscale cloud provider plugin. Sets up cloud resources before delegation."""
    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.uses_config = True

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        self._use_static_config()


class CloudscaleCloudEnvironment(CloudEnvironment):
    """Cloudscale cloud environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        parser = configparser.ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(
            CLOUDSCALE_API_TOKEN=parser.get('default', 'cloudscale_api_token'),
        )

        display.sensitive.add(env_vars['CLOUDSCALE_API_TOKEN'])

        ansible_vars = dict(
            cloudscale_resource_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict((key.lower(), value) for key, value in env_vars.items()))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
