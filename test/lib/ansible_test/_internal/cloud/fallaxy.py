"""Fallaxy (ansible-galaxy) plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import uuid

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
)


class FallaxyProvider(CloudProvider):
    """Fallaxy plugin.

    Sets up Fallaxy (ansible-galaxy) stub server for tests.

    It's source source itself resides at: https://github.com/ansible/fallaxy-test-container
    """

    DOCKER_SIMULATOR_NAME = 'fallaxy-stub'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(FallaxyProvider, self).__init__(args)

        if os.environ.get('ANSIBLE_FALLAXY_CONTAINER'):
            self.image = os.environ.get('ANSIBLE_FALLAXY_CONTAINER')
        else:
            self.image = 'quay.io/ansible/fallaxy-test-container:1.0.0'
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
            display.warning('Excluding tests marked "%s" which require the "%s" command: %s'
                            % (skip.rstrip('/'), docker_cmd, ', '.join(skipped)))

    def setup(self):
        """Setup cloud resource before delegation and reg cleanup callback."""
        super(FallaxyProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_docker_run_options(self):
        """Get additional options needed when delegating tests to a container.

        :rtype: list[str]
        """
        return ['--link', self.DOCKER_SIMULATOR_NAME] if self.managed else []

    def cleanup(self):
        """Clean up the resource and temporary configs files after tests."""
        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(FallaxyProvider, self).cleanup()

    def _setup_dynamic(self):
        container_id = get_docker_container_id()

        if container_id:
            display.info('Running in docker container: %s' % container_id, verbosity=1)

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        display.info('%s Fallaxy simulator docker container.'
                     % ('Using the existing' if results else 'Starting a new'),
                     verbosity=1)

        fallaxy_port = 8080
        fallaxy_token = str(uuid.uuid4()).replace('-', '')

        if not results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(fallaxy_port),) * 2),
                ]

            if not os.environ.get('ANSIBLE_FALLAXY_CONTAINER'):
                docker_pull(self.args, self.image)

            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name, '-e', 'FALLAXY_TOKEN=%s' % fallaxy_token] + publish_ports,
            )

        if self.args.docker:
            fallaxy_host = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            fallaxy_host = self._get_simulator_address()
            display.info('Found Fallaxy simulator container address: %s' % fallaxy_host, verbosity=1)
        else:
            fallaxy_host = 'localhost'

        self._set_cloud_config('FALLAXY_HOST', fallaxy_host)
        self._set_cloud_config('FALLAXY_PORT', str(fallaxy_port))
        self._set_cloud_config('FALLAXY_TOKEN', fallaxy_token)

    def _get_simulator_address(self):
        results = docker_inspect(self.args, self.container_name)
        ipaddress = results[0]['NetworkSettings']['IPAddress']
        return ipaddress

    def _setup_static(self):
        raise NotImplementedError()


class FallaxyEnvironment(CloudEnvironment):
    """Fallaxy environment plugin.

    Updates integration test environment after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        fallaxy_token = self._get_cloud_config('FALLAXY_TOKEN')
        fallaxy_host = self._get_cloud_config('FALLAXY_HOST')
        fallaxy_port = self._get_cloud_config('FALLAXY_PORT')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                fallaxy_token=fallaxy_token,
                fallaxy_galaxy_server='http://%s:%s/api/' % (fallaxy_host, fallaxy_port),
                fallaxy_ah_server='http://%s:%s/api/automation-hub/' % (fallaxy_host, fallaxy_port),
            ),
            env_vars=dict(
                FALLAXY_TOKEN=fallaxy_token,
                FALLAXY_GALAXY_SERVER='http://%s:%s/api/' % (fallaxy_host, fallaxy_port),
                FALLAXY_AH_SERVER='http://%s:%s/api/automation-hub/' % (fallaxy_host, fallaxy_port),
            ),
        )
