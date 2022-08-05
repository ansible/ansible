"""Hetzner Cloud plugin for integration tests."""
from __future__ import annotations

import configparser

from ....util import (
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


class HcloudCloudProvider(CloudProvider):
    """Hetzner Cloud provider plugin. Sets up cloud resources before delegation."""
    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

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

    def _setup_dynamic(self) -> None:
        """Request Hetzner credentials through the Ansible Core CI service."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        config = self._read_config_template()

        aci = self._create_ansible_core_ci()

        response = aci.start()

        if not self.args.explain:
            token = response['hetzner']['token']

            display.sensitive.add(token)
            display.info('Hetzner Cloud Token: %s' % token, verbosity=1)

            values = dict(
                TOKEN=token,
            )

            display.sensitive.add(values['TOKEN'])

            config = self._populate_config_template(config, values)

        self._write_config(config)

    def _create_ansible_core_ci(self) -> AnsibleCoreCI:
        """Return a Heztner instance of AnsibleCoreCI."""
        return AnsibleCoreCI(self.args, CloudResource(platform='hetzner'))


class HcloudCloudEnvironment(CloudEnvironment):
    """Hetzner Cloud cloud environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        parser = configparser.ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(
            HCLOUD_TOKEN=parser.get('default', 'hcloud_api_token'),
        )

        display.sensitive.add(env_vars['HCLOUD_TOKEN'])

        ansible_vars = dict(
            hcloud_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict((key.lower(), value) for key, value in env_vars.items()))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
