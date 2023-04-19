"""VMware vCenter plugin for integration tests."""
from __future__ import annotations

import configparser

from ....util import (
    ApplicationError,
    display,
)

from ....config import (
    IntegrationConfig,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class VcenterProvider(CloudProvider):
    """VMware vcenter/esx plugin. Sets up cloud resources for tests."""

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.uses_config = True

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        if not self._use_static_config():
            raise ApplicationError('Configuration file does not exist: %s' % self.config_static_path)


class VcenterEnvironment(CloudEnvironment):
    """VMware vcenter/esx environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        # We may be in a container, so we cannot just reach VMWARE_TEST_PLATFORM,
        # We do a try/except instead
        parser = configparser.ConfigParser()
        parser.read(self.config_path)  # static

        ansible_vars = dict(
            resource_prefix=self.resource_prefix,
        )
        ansible_vars.update(dict(parser.items('DEFAULT', raw=True)))

        for key, value in ansible_vars.items():
            if key.endswith('_password'):
                display.sensitive.add(value)

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
            module_defaults={
                'group/vmware': {
                    'hostname': ansible_vars['vcenter_hostname'],
                    'username': ansible_vars['vcenter_username'],
                    'password': ansible_vars['vcenter_password'],
                    'port': ansible_vars.get('vcenter_port', '443'),
                    'validate_certs': ansible_vars.get('vmware_validate_certs', 'no'),
                },
            },
        )
