"""OpenNebula plugin for integration tests."""

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment
)

from lib.util import (
    find_executable,
    ApplicationError,
    display,
    is_shippable,
)


class OpenNebulaCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""

    def filter(self, targets, exclude):
        """ no need to filter modules, they can either run from config file or from fixtures"""
        pass

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(OpenNebulaCloudProvider, self).setup()

        if not self._use_static_config():
            self._setup_dynamic()

    def _setup_dynamic(self):
        display.info('No config file provided, will run test from fixtures')

        config = self._read_config_template()
        values = dict(
            URL="http://localhost/RPC2",
            USERNAME='oneadmin',
            PASSWORD='onepass',
            FIXTURES='true',
            REPLAY='true',
        )
        config = self._populate_config_template(config, values)
        self._write_config(config)


class OpenNebulaCloudEnvironment(CloudEnvironment):
    """
    Updates integration test environment after delegation. Will setup the config file as parameter.
    """

    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)
