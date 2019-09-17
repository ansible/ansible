"""OpenNebula plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    display,
    ConfigParser,
)


class OpenNebulaCloudProvider(CloudProvider):
    """Checks if a configuration file has been passed or fixtures are going to be used for testing"""

    def filter(self, targets, exclude):
        """ no need to filter modules, they can either run from config file or from fixtures"""

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
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        ansible_vars = dict(
            resource_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict(parser.items('default')))

        display.sensitive.add(ansible_vars.get('opennebula_password'))

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
