"""NIOS plugin for integration tests."""
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


class NiosProvider(CloudProvider):
    """Nios plugin.

    Sets up NIOS mock server for tests.
    """

    DOCKER_SIMULATOR_NAME = 'nios-simulator'

    DOCKER_IMAGE = 'quay.io/ansible/nios-test-container:1.3.0'
    """Default image to run the nios simulator.

    The simulator must be pinned to a specific version
    to guarantee CI passes with the version used.

    It's source source itself resides at:
    https://github.com/ansible/nios-test-container
    """

    def __init__(self, args):
        """Set up container references for provider.
        :type args: TestConfig
        """
        super(NiosProvider, self).__init__(args)

        self.__container_from_env = os.environ.get('ANSIBLE_NIOSSIM_CONTAINER')
        """Overrides target container, might be used for development.

        Use ANSIBLE_NIOSSIM_CONTAINER=whatever_you_want if you want
        to use other image. Omit/empty otherwise.
        """

        self.image = self.__container_from_env or self.DOCKER_IMAGE

        self.uses_docker = True

    def setup(self):
        """Setup cloud resource before delegation and reg cleanup callback."""
        super(NiosProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_dynamic(self):
        """Spawn a NIOS simulator within docker container."""
        nios_port = 443

        ports = [
            nios_port,
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

        self._set_cloud_config('NIOS_HOST', self.DOCKER_SIMULATOR_NAME)

    def _setup_static(self):
        raise NotImplementedError()


class NiosEnvironment(CloudEnvironment):
    """NIOS environment plugin.

    Updates integration test environment after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        ansible_vars = dict(
            nios_provider=dict(
                host=self._get_cloud_config('NIOS_HOST'),
                username='admin',
                password='infoblox',
            ),
        )

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
