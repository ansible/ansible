"""Azure plugin for integration tests."""
from __future__ import absolute_import, print_function

import json
import os

from lib.util import (
    ApplicationError,
    display,
    is_shippable,
)

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


class AzureCloudProvider(CloudProvider):
    """Azure cloud provider plugin. Sets up cloud resources before delegation."""
    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        if is_shippable():
            return

        # super(AzureCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(AzureCloudProvider, self).setup()

        azure_config_path = os.path.expanduser('~/.azure_ansi')

        if os.path.exists(azure_config_path) and not self.args.docker and not self.args.remote:
            raise ApplicationError('Rename "%s" or use the --docker or --remote option to isolate tests.' % azure_config_path)

        if not self._use_static_config():
            self._setup_dynamic()

    def _setup_dynamic(self):
        """Request Azure credentials through Sherlock."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        config = self._read_config_template()

        sherlock_url = os.environ['SHERLOCK_URL']
        sherlock_key = os.environ['SHERLOCK_KEY']

        azure_values = json.loads(urlopen(sherlock_url + '?code=' + sherlock_key).read().decode('utf-8'))

        if not self.args.explain:
            values = dict(
                CLIENT_ID=azure_values['clientId'],
                CLIENT_SECRET=azure_values['clientSecret'],
                SUBSCRIPTION_ID=azure_values['subscriptionId'],
                TENANT_ID=azure_values['tenantId'],
                # TODO: supports only a single res group, should support multiple
                RESOURCE_GROUPS=azure_values['resourceGroupNames'][0]
            )

            config = self._populate_config_template(config, values)

        self._write_config(config)


class AzureCloudEnvironment(CloudEnvironment):
    """Azure cloud environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)

    def on_failure(self, target, tries):
        """
        :type target: TestTarget
        :type tries: int
        """
        if not tries and self.managed:
            display.notice('If %s failed due to permissions, the IAM test policy may need to be updated. '
                           'For help, consult @mattclay or @gundalow on GitHub or #ansible-devel on IRC.' % target.name)

    @property
    def inventory_hosts(self):
        """
        :rtype: str | None
        """
        return 'azure'
