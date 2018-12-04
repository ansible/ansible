"""Azure plugin for integration tests."""
from __future__ import absolute_import, print_function

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

from lib.http import (
    HttpClient,
    urlparse,
    urlunparse,
    parse_qs,
)

from lib.core_ci import (
    AnsibleCoreCI,
)


class AzureCloudProvider(CloudProvider):
    """Azure cloud provider plugin. Sets up cloud resources before delegation."""
    SHERLOCK_CONFIG_PATH = os.path.expanduser('~/.ansible-sherlock-ci.cfg')

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(AzureCloudProvider, self).__init__(args)

        self.aci = None

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        aci = self._create_ansible_core_ci()

        if os.path.isfile(aci.ci_key):
            return

        if os.path.isfile(self.SHERLOCK_CONFIG_PATH):
            return

        if is_shippable():
            return

        super(AzureCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(AzureCloudProvider, self).setup()

        if not self._use_static_config():
            self._setup_dynamic()

        get_config(self.config_path)  # check required variables

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.aci:
            self.aci.stop()

        super(AzureCloudProvider, self).cleanup()

    def _setup_dynamic(self):
        """Request Azure credentials through Sherlock."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        config = self._read_config_template()
        response = {}

        if os.path.isfile(self.SHERLOCK_CONFIG_PATH):
            with open(self.SHERLOCK_CONFIG_PATH, 'r') as sherlock_fd:
                sherlock_uri = sherlock_fd.readline().strip() + '&rgcount=2'

            parts = urlparse(sherlock_uri)
            query_string = parse_qs(parts.query)
            base_uri = urlunparse(parts[:4] + ('', ''))

            if 'code' not in query_string:
                example_uri = 'https://example.azurewebsites.net/api/sandbox-provisioning'
                raise ApplicationError('The Sherlock URI must include the API key in the query string. Example: %s?code=xxx' % example_uri)

            display.info('Initializing azure/sherlock from: %s' % base_uri, verbosity=1)

            http = HttpClient(self.args)
            result = http.get(sherlock_uri)

            display.info('Started azure/sherlock from: %s' % base_uri, verbosity=1)

            if not self.args.explain:
                response = result.json()
        else:
            aci = self._create_ansible_core_ci()

            aci_result = aci.start()

            if not self.args.explain:
                response = aci_result['azure']
                self.aci = aci

        if not self.args.explain:
            values = dict(
                AZURE_CLIENT_ID=response['clientId'],
                AZURE_SECRET=response['clientSecret'],
                AZURE_SUBSCRIPTION_ID=response['subscriptionId'],
                AZURE_TENANT=response['tenantId'],
                RESOURCE_GROUP=response['resourceGroupNames'][0],
                RESOURCE_GROUP_SECONDARY=response['resourceGroupNames'][1],
            )

            config = '\n'.join('%s: %s' % (key, values[key]) for key in sorted(values))

        self._write_config(config)

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'azure', 'azure', persist=False, stage=self.args.remote_stage, provider=self.args.remote_provider)


class AzureCloudEnvironment(CloudEnvironment):
    """Azure cloud environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        config = get_config(self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)
        cmd.append('-e')
        cmd.append('resource_group=%s' % config['RESOURCE_GROUP'])
        cmd.append('-e')
        cmd.append('resource_group_secondary=%s' % config['RESOURCE_GROUP_SECONDARY'])

        for key in config:
            env[key] = config[key]

    def on_failure(self, target, tries):
        """
        :type target: TestTarget
        :type tries: int
        """
        if not tries and self.managed:
            display.notice('If %s failed due to permissions, the test policy may need to be updated. '
                           'For help, consult @mattclay or @gundalow on GitHub or #ansible-devel on IRC.' % target.name)

    @property
    def inventory_hosts(self):
        """
        :rtype: str | None
        """
        return 'azure'


def get_config(config_path):
    """
    :type config_path: str
    :rtype: dict[str, str]
    """
    with open(config_path, 'r') as config_fd:
        lines = [line for line in config_fd.read().splitlines() if ':' in line and line.strip() and not line.strip().startswith('#')]
        config = dict((kvp[0].strip(), kvp[1].strip()) for kvp in [line.split(':', 1) for line in lines])

    rg_vars = (
        'RESOURCE_GROUP',
        'RESOURCE_GROUP_SECONDARY',
    )

    sp_vars = (
        'AZURE_CLIENT_ID',
        'AZURE_SECRET',
        'AZURE_SUBSCRIPTION_ID',
        'AZURE_TENANT',
    )

    ad_vars = (
        'AZURE_AD_USER',
        'AZURE_PASSWORD',
        'AZURE_SUBSCRIPTION_ID',
    )

    rg_ok = all(var in config for var in rg_vars)
    sp_ok = all(var in config for var in sp_vars)
    ad_ok = all(var in config for var in ad_vars)

    if not rg_ok:
        raise ApplicationError('Resource groups must be defined with: %s' % ', '.join(sorted(rg_vars)))

    if not sp_ok and not ad_ok:
        raise ApplicationError('Credentials must be defined using either:\nService Principal: %s\nActive Directory: %s' % (
            ', '.join(sorted(sp_vars)), ', '.join(sorted(ad_vars))))

    return config
