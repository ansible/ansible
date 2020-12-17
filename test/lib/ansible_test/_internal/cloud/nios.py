"""NIOS plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    find_executable,
    display,
)

from ..docker_util import (
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    get_docker_container_id,
    get_docker_hostname,
    get_docker_container_ip,
    get_docker_preferred_network_name,
    is_docker_user_defined_network,
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
        self.container_name = ''

    def filter(self, targets, exclude):
        """Filter out the tests with the necessary config and res unavailable.

        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        docker_cmd = 'docker'
        docker = find_executable(docker_cmd, required=False)

        if docker:
            return

        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)
            display.warning(
                'Excluding tests marked "%s" '
                'which require the "%s" command: %s'
                % (skip.rstrip('/'), docker_cmd, ', '.join(skipped))
            )

    def setup(self):
        """Setup cloud resource before delegation and reg cleanup callback."""
        super(NiosProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_docker_run_options(self):
        """Get additional options needed when delegating tests to a container.

        :rtype: list[str]
        """
        network = get_docker_preferred_network_name(self.args)

        if self.managed and not is_docker_user_defined_network(network):
            return ['--link', self.DOCKER_SIMULATOR_NAME]

        return []

    def cleanup(self):
        """Clean up the resource and temporary configs files after tests."""
        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(NiosProvider, self).cleanup()

    def _setup_dynamic(self):
        """Spawn a NIOS simulator within docker container."""
        nios_port = 443
        container_id = get_docker_container_id()

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        display.info(
            '%s NIOS simulator docker container.'
            % ('Using the existing' if results else 'Starting a new'),
            verbosity=1,
        )

        if not results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(nios_port), ) * 2),
                ]

            if not self.__container_from_env:
                docker_pull(self.args, self.image)

            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name] + publish_ports,
            )

        if self.args.docker:
            nios_host = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            nios_host = self._get_simulator_address()
            display.info(
                'Found NIOS simulator container address: %s'
                % nios_host, verbosity=1
            )
        else:
            nios_host = get_docker_hostname()

        self._set_cloud_config('NIOS_HOST', nios_host)

    def _get_simulator_address(self):
        return get_docker_container_ip(self.args, self.container_name)

    def _setup_static(self):
        raise NotImplementedError


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
