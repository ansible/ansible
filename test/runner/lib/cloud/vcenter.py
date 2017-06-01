"""CloudStack plugin for integration tests."""
from __future__ import absolute_import, print_function

import json
import os
import re
import time

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

from lib.util import (
    find_executable,
    ApplicationError,
    display,
    SubprocessError,
    is_shippable,
)

from lib.http import (
    HttpClient,
    urlparse,
)

from lib.docker_util import (
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    docker_network_inspect,
    get_docker_container_id,
)

try:
    # noinspection PyPep8Naming
    import ConfigParser as configparser
except ImportError:
    # noinspection PyUnresolvedReferences
    import configparser


class VcenterProvider(CloudProvider):
    """CloudStack cloud provider plugin. Sets up cloud resources before delegation."""
    DOCKER_SIMULATOR_NAME = 'vcsim'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VcenterProvider, self).__init__(args, config_extension='.ini')

        self.image = 'jctanner:vcenter-simulator'
        self.container_name = ''
        self.endpoint = ''
        self.vcenter_host = None
        self.host = ''
        self.port = 0

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
            if is_shippable():
                docker_rm(self.args, self.container_name)
            elif not self.args.explain:
                display.notice('Remember to run `docker rm -f %s` when finished testing.' % self.container_name)

        super(VcenterProvider, self).cleanup()

    def _setup_dynamic(self):
        """Create a vcenter simulator using docker."""
        self.container_name = self.DOCKER_SIMULATOR_NAME
        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        if results:
            display.info('Using the existing Vcenter simulator docker container.', verbosity=1)
        else:
            display.info('Starting a new Vcenter simulator docker container.', verbosity=1)
            #docker_pull(self.args, self.image)
            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name]
            )

        self.vcenter_host = self._get_simulator_address()
        self._set_cloud_config('vcenter_host', self.vcenter_host)

    def _get_simulator_address(self):
        results = docker_inspect(self.args, self.container_name)
        ipaddress = results[0]['NetworkSettings']['IPAddress']
        return ipaddress

    def _read_config_template(self):
        pass

    def _wait_for_service(self):
        pass

    def _get_credentials(self):
        pass


class VcenterEnvironment(CloudEnvironment):
    """CloudStack cloud environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """

        # Send the container IP down to the integration test(s)
        env['vcenter_host'] = self._get_cloud_config('vcenter_host')
