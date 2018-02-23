"""OpenShift plugin for integration tests."""
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
)

from lib.http import (
    HttpClient,
)

from lib.docker_util import (
    docker_exec,
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    docker_network_inspect,
    get_docker_container_id,
)


class OpenShiftCloudProvider(CloudProvider):
    """OpenShift cloud provider plugin. Sets up cloud resources before delegation."""
    DOCKER_CONTAINER_NAME = 'openshift-origin'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(OpenShiftCloudProvider, self).__init__(args, config_extension='.kubeconfig')

        # The image must be pinned to a specific version to guarantee CI passes with the version used.
        self.image = 'openshift/origin:v3.7.1'
        self.container_name = ''

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        docker = find_executable('docker', required=False)

        if docker:
            return

        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require the "docker" command or config (see "%s"): %s'
                            % (skip.rstrip('/'), self.config_template_path, ', '.join(skipped)))

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(OpenShiftCloudProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_remote_ssh_options(self):
        """Get any additional options needed when delegating tests to a remote instance via SSH.
        :rtype: list[str]
        """
        if self.managed:
            return ['-R', '8443:localhost:8443']

        return []

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker container.
        :rtype: list[str]
        """
        if self.managed:
            return ['--link', self.DOCKER_CONTAINER_NAME]

        return []

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(OpenShiftCloudProvider, self).cleanup()

    def _setup_static(self):
        """Configure OpenShift tests for use with static configuration."""
        with open(self.config_static_path, 'r') as config_fd:
            config = config_fd.read()

        match = re.search(r'^ *server: (?P<server>.*)$', config, flags=re.MULTILINE)

        if match:
            endpoint = match.group('server')
            self._wait_for_service(endpoint)
        else:
            display.warning('Could not find OpenShift endpoint in kubeconfig. Skipping check for OpenShift service availability.')

    def _setup_dynamic(self):
        """Create a OpenShift container using docker."""
        self.container_name = self.DOCKER_CONTAINER_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0]['State']['Running']:
            docker_rm(self.args, self.container_name)
            results = []

        if results:
            display.info('Using the existing OpenShift docker container.', verbosity=1)
        else:
            display.info('Starting a new OpenShift docker container.', verbosity=1)
            docker_pull(self.args, self.image)
            cmd = ['start', 'master', '--listen', 'https://0.0.0.0:8443']
            docker_run(self.args, self.image, ['-d', '-p', '8443:8443', '--name', self.container_name], cmd)

        container_id = get_docker_container_id()

        if container_id:
            display.info('Running in docker container: %s' % container_id, verbosity=1)
            host = self._get_container_address()
            display.info('Found OpenShift container address: %s' % host, verbosity=1)
        else:
            host = 'localhost'

        port = 8443
        endpoint = 'https://%s:%s/' % (host, port)

        self._wait_for_service(endpoint)

        if self.args.explain:
            config = '# Unknown'
        else:
            if self.args.docker:
                host = self.DOCKER_CONTAINER_NAME

            server = 'https://%s:%s' % (host, port)
            config = self._get_config(server)

        self._write_config(config)

    def _get_container_address(self):
        networks = docker_network_inspect(self.args, 'bridge')

        try:
            bridge = [network for network in networks if network['Name'] == 'bridge'][0]
            containers = bridge['Containers']
            container = [containers[container] for container in containers if containers[container]['Name'] == self.DOCKER_CONTAINER_NAME][0]
            return re.sub(r'/[0-9]+$', '', container['IPv4Address'])
        except Exception:
            display.error('Failed to process the following docker network inspect output:\n%s' %
                          json.dumps(networks, indent=4, sort_keys=True))
            raise

    def _wait_for_service(self, endpoint):
        """Wait for the OpenShift service endpoint to accept connections.
        :type endpoint: str
        """
        if self.args.explain:
            return

        client = HttpClient(self.args, always=True, insecure=True)
        endpoint = endpoint

        for dummy in range(1, 30):
            display.info('Waiting for OpenShift service: %s' % endpoint, verbosity=1)

            try:
                client.get(endpoint)
                return
            except SubprocessError:
                pass

            time.sleep(10)

        raise ApplicationError('Timeout waiting for OpenShift service.')

    def _get_config(self, server):
        """Get OpenShift config from container.
        :type server: str
        :rtype: dict[str, str]
        """
        cmd = ['cat', '/var/lib/origin/openshift.local.config/master/admin.kubeconfig']

        stdout, dummy = docker_exec(self.args, self.container_name, cmd, capture=True)

        config = stdout
        config = re.sub(r'^( *)certificate-authority-data: .*$', r'\1insecure-skip-tls-verify: true', config, flags=re.MULTILINE)
        config = re.sub(r'^( *)server: .*$', r'\1server: %s' % server, config, flags=re.MULTILINE)

        return config


class OpenShiftCloudEnvironment(CloudEnvironment):
    """OpenShift cloud environment plugin. Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        changes = dict(
            K8S_AUTH_KUBECONFIG=self.config_path,
        )

        env.update(changes)
