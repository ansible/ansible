"""ACME plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    find_executable,
    display,
    ApplicationError,
    SubprocessError,
)

from ..http import (
    HttpClient,
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


class ACMEProvider(CloudProvider):
    """ACME plugin. Sets up cloud resources for tests."""
    DOCKER_SIMULATOR_NAME = 'acme-simulator'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(ACMEProvider, self).__init__(args)

        # The simulator must be pinned to a specific version to guarantee CI passes with the version used.
        if os.environ.get('ANSIBLE_ACME_CONTAINER'):
            self.image = os.environ.get('ANSIBLE_ACME_CONTAINER')
        else:
            self.image = 'quay.io/ansible/acme-test-container:2.0.0'
        self.container_name = ''

    def _wait_for_service(self, protocol, acme_host, port, local_part, name):
        """Wait for an endpoint to accept connections."""
        if self.args.explain:
            return

        client = HttpClient(self.args, always=True, insecure=True)
        endpoint = '%s://%s:%d/%s' % (protocol, acme_host, port, local_part)

        for dummy in range(1, 30):
            display.info('Waiting for %s: %s' % (name, endpoint), verbosity=1)

            try:
                client.get(endpoint)
                return
            except SubprocessError:
                pass

            time.sleep(1)

        raise ApplicationError('Timeout waiting for %s.' % name)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        docker = find_executable('docker', required=False)

        if docker:
            return

        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require the "docker" command: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(ACMEProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker container.
        :rtype: list[str]
        """
        network = get_docker_preferred_network_name(self.args)

        if self.managed and not is_docker_user_defined_network(network):
            return ['--link', self.DOCKER_SIMULATOR_NAME]

        return []

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(ACMEProvider, self).cleanup()

    def _setup_dynamic(self):
        """Create a ACME test container using docker."""
        container_id = get_docker_container_id()

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        if results:
            display.info('Using the existing ACME docker test container.', verbosity=1)
        else:
            display.info('Starting a new ACME docker test container.', verbosity=1)

            if not container_id:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', '5000:5000',  # control port for flask app in container
                    '-p', '14000:14000',  # Pebble ACME CA
                ]
            else:
                publish_ports = []

            if not os.environ.get('ANSIBLE_ACME_CONTAINER'):
                docker_pull(self.args, self.image)

            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name] + publish_ports,
            )

        if self.args.docker:
            acme_host = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            acme_host = self._get_simulator_address()
            display.info('Found ACME test container address: %s' % acme_host, verbosity=1)
        else:
            acme_host = get_docker_hostname()

        if container_id:
            acme_host_ip = self._get_simulator_address()
        else:
            acme_host_ip = get_docker_hostname()

        self._set_cloud_config('acme_host', acme_host)

        self._wait_for_service('http', acme_host_ip, 5000, '', 'ACME controller')
        self._wait_for_service('https', acme_host_ip, 14000, 'dir', 'ACME CA endpoint')

    def _get_simulator_address(self):
        return get_docker_container_ip(self.args, self.container_name)

    def _setup_static(self):
        raise NotImplementedError()


class ACMEEnvironment(CloudEnvironment):
    """ACME environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        ansible_vars = dict(
            acme_host=self._get_cloud_config('acme_host'),
        )

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
        )
