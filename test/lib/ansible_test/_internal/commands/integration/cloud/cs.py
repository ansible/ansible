"""CloudStack plugin for integration tests."""
from __future__ import annotations

import json
import configparser
import os
import urllib.parse
import typing as t

from ....util import (
    ApplicationError,
    display,
)

from ....config import (
    IntegrationConfig,
)

from ....docker_util import (
    docker_exec,
)

from ....containers import (
    CleanupMode,
    run_support_container,
    wait_for_file,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class CsCloudProvider(CloudProvider):
    """CloudStack cloud provider plugin. Sets up cloud resources before delegation."""

    DOCKER_SIMULATOR_NAME = 'cloudstack-sim'

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.image = os.environ.get('ANSIBLE_CLOUDSTACK_CONTAINER', 'quay.io/ansible/cloudstack-test-container:1.4.0')
        self.host = ''
        self.port = 0

        self.uses_docker = True
        self.uses_config = True

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_static(self) -> None:
        """Configure CloudStack tests for use with static configuration."""
        parser = configparser.ConfigParser()
        parser.read(self.config_static_path)

        endpoint = parser.get('cloudstack', 'endpoint')

        parts = urllib.parse.urlparse(endpoint)

        self.host = parts.hostname

        if not self.host:
            raise ApplicationError('Could not determine host from endpoint: %s' % endpoint)

        if parts.port:
            self.port = parts.port
        elif parts.scheme == 'http':
            self.port = 80
        elif parts.scheme == 'https':
            self.port = 443
        else:
            raise ApplicationError('Could not determine port from endpoint: %s' % endpoint)

        display.info('Read cs host "%s" and port %d from config: %s' % (self.host, self.port, self.config_static_path), verbosity=1)

    def _setup_dynamic(self) -> None:
        """Create a CloudStack simulator using docker."""
        config = self._read_config_template()

        self.port = 8888

        ports = [
            self.port,
        ]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            self.DOCKER_SIMULATOR_NAME,
            ports,
            allow_existing=True,
            cleanup=CleanupMode.YES,
        )

        if not descriptor:
            return

        # apply work-around for OverlayFS issue
        # https://github.com/docker/for-linux/issues/72#issuecomment-319904698
        docker_exec(self.args, self.DOCKER_SIMULATOR_NAME, ['find', '/var/lib/mysql', '-type', 'f', '-exec', 'touch', '{}', ';'], capture=True)

        if self.args.explain:
            values = dict(
                HOST=self.host,
                PORT=str(self.port),
            )
        else:
            credentials = self._get_credentials(self.DOCKER_SIMULATOR_NAME)

            values = dict(
                HOST=self.DOCKER_SIMULATOR_NAME,
                PORT=str(self.port),
                KEY=credentials['apikey'],
                SECRET=credentials['secretkey'],
            )

            display.sensitive.add(values['SECRET'])

        config = self._populate_config_template(config, values)

        self._write_config(config)

    def _get_credentials(self, container_name: str) -> dict[str, t.Any]:
        """Wait for the CloudStack simulator to return credentials."""

        def check(value) -> bool:
            """Return True if the given configuration is valid JSON, otherwise return False."""
            # noinspection PyBroadException
            try:
                json.loads(value)
            except Exception:  # pylint: disable=broad-except
                return False  # sometimes the file exists but is not yet valid JSON

            return True

        stdout = wait_for_file(self.args, container_name, '/var/www/html/admin.json', sleep=10, tries=30, check=check)

        return json.loads(stdout)


class CsCloudEnvironment(CloudEnvironment):
    """CloudStack cloud environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        parser = configparser.ConfigParser()
        parser.read(self.config_path)

        config = dict(parser.items('default'))

        env_vars = dict(
            CLOUDSTACK_ENDPOINT=config['endpoint'],
            CLOUDSTACK_KEY=config['key'],
            CLOUDSTACK_SECRET=config['secret'],
            CLOUDSTACK_TIMEOUT=config['timeout'],
        )

        display.sensitive.add(env_vars['CLOUDSTACK_SECRET'])

        ansible_vars = dict(
            cs_resource_prefix=self.resource_prefix,
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
