"""OpenShift plugin for integration tests."""
from __future__ import annotations

import re

from ....io import (
    read_text_file,
)

from ....util import (
    display,
)

from ....config import (
    IntegrationConfig,
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


class OpenShiftCloudProvider(CloudProvider):
    """OpenShift cloud provider plugin. Sets up cloud resources before delegation."""
    DOCKER_CONTAINER_NAME = 'openshift-origin'

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args, config_extension='.kubeconfig')

        # The image must be pinned to a specific version to guarantee CI passes with the version used.
        self.image = 'quay.io/ansible/openshift-origin:v3.9.0'

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
        """Configure OpenShift tests for use with static configuration."""
        config = read_text_file(self.config_static_path)

        match = re.search(r'^ *server: (?P<server>.*)$', config, flags=re.MULTILINE)

        if not match:
            display.warning('Could not find OpenShift endpoint in kubeconfig.')

    def _setup_dynamic(self) -> None:
        """Create a OpenShift container using docker."""
        port = 8443

        ports = [
            port,
        ]

        cmd = ['start', 'master', '--listen', 'https://0.0.0.0:%d' % port]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            self.DOCKER_CONTAINER_NAME,
            ports,
            allow_existing=True,
            cleanup=CleanupMode.YES,
            cmd=cmd,
        )

        if not descriptor:
            return

        if self.args.explain:
            config = '# Unknown'
        else:
            config = self._get_config(self.DOCKER_CONTAINER_NAME, 'https://%s:%s/' % (self.DOCKER_CONTAINER_NAME, port))

        self._write_config(config)

    def _get_config(self, container_name: str, server: str) -> str:
        """Get OpenShift config from container."""
        stdout = wait_for_file(self.args, container_name, '/var/lib/origin/openshift.local.config/master/admin.kubeconfig', sleep=10, tries=30)

        config = stdout
        config = re.sub(r'^( *)certificate-authority-data: .*$', r'\1insecure-skip-tls-verify: true', config, flags=re.MULTILINE)
        config = re.sub(r'^( *)server: .*$', r'\1server: %s' % server, config, flags=re.MULTILINE)

        return config


class OpenShiftCloudEnvironment(CloudEnvironment):
    """OpenShift cloud environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        env_vars = dict(
            K8S_AUTH_KUBECONFIG=self.config_path,
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
        )
