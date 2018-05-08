"""OpenNebula plugin for integration tests."""

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment
)

from lib.util import (
    ApplicationError,
    display,
    is_shippable,
)

class OpenNebulaCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""
    def filter(self, targets, exclude):
        """This will filter out tests that cannot be run becuase dont have the reuired configuration"""
        if os.path.isfile(self.config_static_path):
            return

        super(OpenNebulaCloudProvider,self).filter(targets,exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(OpenNebulaCloudProvider, self).setup()

        if not self._use_static_config():
            display.notice(
                'static configuration could not be used. are you missing a template file?'
            )


class OpenNebulaCloudEnvironment(CloudEnvironment):

    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)