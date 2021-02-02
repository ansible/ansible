# Copyright: (c) 2018, Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""GCP plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ..util import (
    display,
    ConfigParser,
)

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)


class GcpCloudProvider(CloudProvider):
    """GCP cloud provider plugin. Sets up cloud resources before delegation."""
    def __init__(self, args):
        """Set up container references for provider.
        :type args: TestConfig
        """
        super(GcpCloudProvider, self).__init__(args)

        self.uses_config = True

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(GcpCloudProvider, self).setup()

        if not self._use_static_config():
            display.notice(
                'static configuration could not be used. are you missing a template file?'
            )


class GcpCloudEnvironment(CloudEnvironment):
    """GCP cloud environment plugin. Updates integration test environment after delegation."""
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

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
