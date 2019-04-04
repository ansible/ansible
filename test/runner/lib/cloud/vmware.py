"""Vmware plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from lib.util import (
    ApplicationError,
    display,
    is_shippable,
    ConfigParser,
)

from lib.core_ci import (
    AnsibleCoreCI,
)


class VmwareCloudProvider(CloudProvider):
    """Vmware cloud provider plugin. Sets up cloud resources before delegation."""

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VmwareCloudProvider, self).__init__(args)
        self.aci = None

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources
        are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """

        if os.path.isfile(self.config_static_path):
            return

        aci = self._create_ansible_core_ci()

        if os.path.isfile(aci.ci_key):
            return

        if is_shippable():
            return

        super(VmwareCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a
        cleanup callback."""
        super(VmwareCloudProvider, self).setup()

        if not self._use_static_config():
            self._setup_dynamic()

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files
        after tests complete."""
        if self.aci:
            self.aci.stop()
        super(VmwareCloudProvider, self).cleanup()

    def _setup_dynamic(self):
        """Request Esxi credentials through the Ansible Core CI service."""
        display.info('Provisioning %s cloud environment.' % self.platform,
                     verbosity=1)

        config = self._read_config_template()

        aci = self._create_ansible_core_ci()

        if not self.args.explain:
            response = aci.start()

        if not self.args.explain:
            credentials = response['esxi']
            self.aci = aci

        if not self.args.explain:
            values = dict(
                VMWARE_HOST=credentials['VMWARE_HOST'],
                VMWARE_USER=credentials['VMWARE_USER'],
                VMWARE_PASSWORD=credentials['VMWARE_PASSWORD'],
                VMWARE_HTTPS_PORT=str(credentials['VMWARE_HTTPS_PORT']),
                VMWARE_SSH_PORT=str(credentials['VMWARE_SSH_PORT']),
                VMWARE_VALIDATE_CERTS=credentials["VMWARE_VALIDATE_CERTS"],
            )

            config = self._populate_config_template(config, values)
            self._write_config(config)

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'Vmware', 'Vmware',
                             persist=False, stage=self.args.remote_stage,
                             provider=self.args.remote_provider)


class VmwareEnvironment(CloudEnvironment):
    """VMware Vmware environment plugin. Updates integration test
    environment after delegation."""
    def get_environment_config(self):
        """
        :rtype: CloudEnvionmentConfig
        """

        parser = ConfigParser()
        parser.read(self.config_path)

        env_vars = {}

        ansible_vars = dict(
            resource_prefix=self.resource_prefix,
        )
        ansible_vars.update(dict(parser.items('DEFAULT')))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
