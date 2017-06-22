"""VMware vCenter plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

from lib.util import (
    find_executable,
    display,
)

from lib.docker_util import (
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    get_docker_container_id,
)

try:
    # noinspection PyPep8Naming
    import ConfigParser as configparser
except ImportError:
    # noinspection PyUnresolvedReferences
    import configparser


class VcenterProvider(CloudProvider):
    """VMware vcenter/esx plugin. Sets up cloud resources for tests."""
    DOCKER_SIMULATOR_NAME = 'vcenter-simulator'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VcenterProvider, self).__init__(args, config_extension='.ini')

        self.image = 'ansible/ansible:vcenter-simulator'
        self.container_name = ''

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        docker = find_executable('docker')

        if docker:
            return

        super(VcenterProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(VcenterProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker container.
        :rtype: list[str]
        """
        if self.managed:
            return ['--link', self.DOCKER_SIMULATOR_NAME]

        return []

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(VcenterProvider, self).cleanup()

    def _setup_dynamic(self):
        """Create a vcenter simulator using docker."""
        container_id = get_docker_container_id()

        if container_id:
            display.info('Running in docker container: %s' % container_id, verbosity=1)

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        if results:
            display.info('Using the existing vCenter simulator docker container.', verbosity=1)
        else:
            display.info('Starting a new vCenter simulator docker container.', verbosity=1)

            if not self.args.docker and not container_id:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', '80:80',
                    '-p', '443:443',
                    '-p', '8080:8080',
                    '-p', '8989:8989',
                    '-p', '5000:5000',  # control port for flask app in simulator
                ]
            else:
                publish_ports = []

            docker_pull(self.args, self.image)
            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name] + publish_ports,
            )

        if self.args.docker:
            vcenter_host = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            vcenter_host = self._get_simulator_address()
            display.info('Found vCenter simulator container address: %s' % vcenter_host, verbosity=1)
        else:
            vcenter_host = 'localhost'

        self._set_cloud_config('vcenter_host', vcenter_host)

    def _get_simulator_address(self):
        results = docker_inspect(self.args, self.container_name)
        ipaddress = results[0]['NetworkSettings']['IPAddress']
        return ipaddress

    def _setup_static(self):
        raise NotImplementedError()


class VcenterEnvironment(CloudEnvironment):
    """VMware vcenter/esx environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """

        # Send the container IP down to the integration test(s)
        env['vcenter_host'] = self._get_cloud_config('vcenter_host')
