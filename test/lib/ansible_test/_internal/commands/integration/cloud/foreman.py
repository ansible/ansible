"""Foreman plugin for integration tests."""
from __future__ import annotations

import os

from ....config import (
    IntegrationConfig,
)

from ....containers import (
    CleanupMode,
    run_support_container,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


class ForemanProvider(CloudProvider):
    """Foreman plugin. Sets up Foreman stub server for tests."""
    DOCKER_SIMULATOR_NAME = 'foreman-stub'

    # Default image to run Foreman stub from.
    #
    # The simulator must be pinned to a specific version
    # to guarantee CI passes with the version used.
    #
    # It's source source itself resides at:
    # https://github.com/ansible/foreman-test-container
    DOCKER_IMAGE = 'quay.io/ansible/foreman-test-container:1.4.0'

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.__container_from_env = os.environ.get('ANSIBLE_FRMNSIM_CONTAINER')
        """
        Overrides target container, might be used for development.

        Use ANSIBLE_FRMNSIM_CONTAINER=whatever_you_want if you want
        to use other image. Omit/empty otherwise.
        """
        self.image = self.__container_from_env or self.DOCKER_IMAGE

        self.uses_docker = True

    def setup(self) -> None:
        """Setup cloud resource before delegation and reg cleanup callback."""
        super().setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_dynamic(self) -> None:
        """Spawn a Foreman stub within docker container."""
        foreman_port = 8080

        ports = [
            foreman_port,
        ]

        run_support_container(
            self.args,
            self.platform,
            self.image,
            self.DOCKER_SIMULATOR_NAME,
            ports,
            allow_existing=True,
            cleanup=CleanupMode.YES,
        )

        self._set_cloud_config('FOREMAN_HOST', self.DOCKER_SIMULATOR_NAME)
        self._set_cloud_config('FOREMAN_PORT', str(foreman_port))

    def _setup_static(self) -> None:
        raise NotImplementedError()


class ForemanEnvironment(CloudEnvironment):
    """Foreman environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        env_vars = dict(
            FOREMAN_HOST=str(self._get_cloud_config('FOREMAN_HOST')),
            FOREMAN_PORT=str(self._get_cloud_config('FOREMAN_PORT')),
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
        )
