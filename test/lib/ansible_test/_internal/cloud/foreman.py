"""Foreman plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..containers import (
    run_support_container,
)


class ForemanProvider(CloudProvider):
    """Foreman plugin.

    Sets up Foreman stub server for tests.
    """

    DOCKER_SIMULATOR_NAME = 'foreman-stub'

    DOCKER_IMAGE = 'quay.io/ansible/foreman-test-container:1.4.0'
    """Default image to run Foreman stub from.

    The simulator must be pinned to a specific version
    to guarantee CI passes with the version used.

    It's source source itself resides at:
    https://github.com/ansible/foreman-test-container
    """

    def __init__(self, args):
        """Set up container references for provider.

        :type args: TestConfig
        """
        super(ForemanProvider, self).__init__(args)

        self.__container_from_env = os.environ.get('ANSIBLE_FRMNSIM_CONTAINER')
        """Overrides target container, might be used for development.

        Use ANSIBLE_FRMNSIM_CONTAINER=whatever_you_want if you want
        to use other image. Omit/empty otherwise.
        """

        self.image = self.__container_from_env or self.DOCKER_IMAGE

        self.uses_docker = True

    def setup(self):
        """Setup cloud resource before delegation and reg cleanup callback."""
        super(ForemanProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_dynamic(self):
        """Spawn a Foreman stub within docker container."""
        foreman_port = 8080

        ports = [
            foreman_port,
        ]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            self.DOCKER_SIMULATOR_NAME,
            ports,
            allow_existing=True,
            cleanup=True,
        )

        descriptor.register(self.args)

        self._set_cloud_config('FOREMAN_HOST', self.DOCKER_SIMULATOR_NAME)
        self._set_cloud_config('FOREMAN_PORT', str(foreman_port))

    def _setup_static(self):
        raise NotImplementedError()


class ForemanEnvironment(CloudEnvironment):
    """Foreman environment plugin.

    Updates integration test environment after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        env_vars = dict(
            FOREMAN_HOST=self._get_cloud_config('FOREMAN_HOST'),
            FOREMAN_PORT=self._get_cloud_config('FOREMAN_PORT'),
        )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
        )
