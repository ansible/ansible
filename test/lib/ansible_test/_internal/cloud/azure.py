"""Azure plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ..io import (
    read_text_file,
)

from ..util import (
    ApplicationError,
    display,
    ConfigParser,
)

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..http import (
    HttpClient,
    urlparse,
    urlunparse,
    parse_qs,
)

from ..core_ci import (
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

        if aci.available:
            return

        if os.path.isfile(self.SHERLOCK_CONFIG_PATH):
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
            sherlock_uri = read_text_file(self.SHERLOCK_CONFIG_PATH).splitlines()[0].strip() + '&rgcount=2'

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

            display.sensitive.add(values['AZURE_SECRET'])

            config = '\n'.join('%s: %s' % (key, values[key]) for key in sorted(values))

            config = '[default]\n' + config

        self._write_config(config)

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'azure', 'azure', persist=False, stage=self.args.remote_stage, provider=self.args.remote_provider)


class AzureCloudEnvironment(CloudEnvironment):
    """Azure cloud environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        env_vars = get_config(self.config_path)

        display.sensitive.add(env_vars.get('AZURE_SECRET'))
        display.sensitive.add(env_vars.get('AZURE_PASSWORD'))

        ansible_vars = dict(
            resource_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict((key.lower(), value) for key, value in env_vars.items()))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )

    def on_failure(self, target, tries):
        """
        :type target: TestTarget
        :type tries: int
        """
        if not tries and self.managed:
            display.notice('If %s failed due to permissions, the test policy may need to be updated. '
                           'For help, consult @mattclay or @gundalow on GitHub or #ansible-devel on IRC.' % target.name)


def get_config(config_path):
    """
    :type config_path: str
    :rtype: dict[str, str]
    """
    parser = ConfigParser()
    parser.read(config_path)

    config = dict((key.upper(), value) for key, value in parser.items('default'))

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
