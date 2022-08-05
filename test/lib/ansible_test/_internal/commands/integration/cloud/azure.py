"""Azure plugin for integration tests."""
from __future__ import annotations

import configparser
import typing as t

from ....util import (
    ApplicationError,
    display,
)

from ....config import (
    IntegrationConfig,
)

from ....target import (
    IntegrationTarget,
)

from ....core_ci import (
    AnsibleCoreCI,
    CloudResource,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class AzureCloudProvider(CloudProvider):
    """Azure cloud provider plugin. Sets up cloud resources before delegation."""
    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.aci: t.Optional[AnsibleCoreCI] = None

        self.uses_config = True

    def filter(self, targets: tuple[IntegrationTarget, ...], exclude: list[str]) -> None:
        """Filter out the cloud tests when the necessary config and resources are not available."""
        aci = self._create_ansible_core_ci()

        if aci.available:
            return

        super().filter(targets, exclude)

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        if not self._use_static_config():
            self._setup_dynamic()

        get_config(self.config_path)  # check required variables

    def cleanup(self) -> None:
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.aci:
            self.aci.stop()

        super().cleanup()

    def _setup_dynamic(self) -> None:
        """Request Azure credentials through ansible-core-ci."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        config = self._read_config_template()
        response = {}

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

    def _create_ansible_core_ci(self) -> AnsibleCoreCI:
        """Return an Azure instance of AnsibleCoreCI."""
        return AnsibleCoreCI(self.args, CloudResource(platform='azure'))


class AzureCloudEnvironment(CloudEnvironment):
    """Azure cloud environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
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

    def on_failure(self, target: IntegrationTarget, tries: int) -> None:
        """Callback to run when an integration target fails."""
        if not tries and self.managed:
            display.notice('If %s failed due to permissions, the test policy may need to be updated.' % target.name)


def get_config(config_path: str) -> dict[str, str]:
    """Return a configuration dictionary parsed from the given configuration path."""
    parser = configparser.ConfigParser()
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
