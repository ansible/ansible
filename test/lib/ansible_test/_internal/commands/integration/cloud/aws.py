"""AWS plugin for integration tests."""
from __future__ import annotations

import os
import uuid
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

from ....host_configs import (
    OriginConfig,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class AwsCloudProvider(CloudProvider):
    """AWS cloud provider plugin. Sets up cloud resources before delegation."""

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

        aws_config_path = os.path.expanduser('~/.aws')

        if os.path.exists(aws_config_path) and isinstance(self.args.controller, OriginConfig):
            raise ApplicationError('Rename "%s" or use the --docker or --remote option to isolate tests.' % aws_config_path)

        if not self._use_static_config():
            self._setup_dynamic()

    def _setup_dynamic(self) -> None:
        """Request AWS credentials through the Ansible Core CI service."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        config = self._read_config_template()

        aci = self._create_ansible_core_ci()

        response = aci.start()

        if not self.args.explain:
            credentials = response['aws']['credentials']

            values = dict(
                ACCESS_KEY=credentials['access_key'],
                SECRET_KEY=credentials['secret_key'],
                SECURITY_TOKEN=credentials['session_token'],
                REGION='us-east-1',
            )

            display.sensitive.add(values['SECRET_KEY'])
            display.sensitive.add(values['SECURITY_TOKEN'])

            config = self._populate_config_template(config, values)

        self._write_config(config)

    def _create_ansible_core_ci(self) -> AnsibleCoreCI:
        """Return an AWS instance of AnsibleCoreCI."""
        return AnsibleCoreCI(self.args, CloudResource(platform='aws'))


class AwsCloudEnvironment(CloudEnvironment):
    """AWS cloud environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        parser = configparser.ConfigParser()
        parser.read(self.config_path)

        ansible_vars: dict[str, t.Any] = dict(
            resource_prefix=self.resource_prefix,
            tiny_prefix=uuid.uuid4().hex[0:12]
        )

        ansible_vars.update(dict(parser.items('default')))

        display.sensitive.add(ansible_vars.get('aws_secret_key'))
        display.sensitive.add(ansible_vars.get('security_token'))

        if 'aws_cleanup' not in ansible_vars:
            ansible_vars['aws_cleanup'] = not self.managed

        env_vars = {'ANSIBLE_DEBUG_BOTOCORE_LOGS': 'True'}

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
            callback_plugins=['aws_resource_actions'],
        )

    def on_failure(self, target: IntegrationTarget, tries: int) -> None:
        """Callback to run when an integration target fails."""
        if not tries and self.managed:
            display.notice('If %s failed due to permissions, the IAM test policy may need to be updated. '
                           'https://docs.ansible.com/ansible/devel/collections/amazon/aws/docsite/dev_guidelines.html#aws-permissions-for-integration-tests'
                           % target.name)
