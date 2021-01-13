"""Hetzner Cloud plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ..util import (
    display,
    ConfigParser,
)

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..core_ci import (
    AnsibleCoreCI,
)


class HcloudCloudProvider(CloudProvider):
    """Hetzner Cloud provider plugin. Sets up cloud resources before
       delegation.
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(HcloudCloudProvider, self).__init__(args)

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

        super(HcloudCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(HcloudCloudProvider, self).setup()

        if not self._use_static_config():
            self._setup_dynamic()

    def _setup_dynamic(self):
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

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'hetzner', 'hetzner', persist=False, stage=self.args.remote_stage, provider='hetzner', internal=True)


class HcloudCloudEnvironment(CloudEnvironment):
    """Hetzner Cloud cloud environment plugin. Updates integration test environment
       after delegation.
    """

    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        parser = ConfigParser()
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
