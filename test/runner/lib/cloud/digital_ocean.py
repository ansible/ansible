"""DigitalOcean plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.util import (
    is_shippable,
)

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)


class DigitalOceanCloudProvider(CloudProvider):
    """DigitalOcean cloud provider plugin. Sets up cloud resources before delegation."""
    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        if is_shippable():
            return

        super(DigitalOceanCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(DigitalOceanCloudProvider, self).setup()

        self._use_static_config()


class DigitalOceanCloudEnvironment(CloudEnvironment):
    """Digital Ocean cloud environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)

    @property
    def inventory_hosts(self):
        """
        :rtype: str | None
        """
        return 'digital_ocean'
