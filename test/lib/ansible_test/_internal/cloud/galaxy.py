"""Galaxy (ansible-galaxy) plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile
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
    docker_command,
    docker_run,
    docker_start,
    docker_rm,
    docker_inspect,
    docker_pull,
    get_docker_container_id,
)


SETTINGS = b'''
CONTENT_ORIGIN='pulp:80'
ANSIBLE_API_HOSTNAME='http://pulp:80'
ANSIBLE_CONTENT_HOSTNAME='http://pulp:80/pulp/content'
TOKEN_AUTH_DISABLED=True
'''

SET_ADMIN_PASSWORD = b'''#!/usr/bin/execlineb -S0
foreground {
  redirfd -w 1 /dev/null
  redirfd -w 2 /dev/null
  export DJANGO_SETTINGS_MODULE pulpcore.app.settings
  export PULP_CONTENT_ORIGIN localhost
  s6-setuidgid postgres
  /usr/local/bin/django-admin reset-admin-password --password password
}
'''


class GalaxyProvider(CloudProvider):
    """Galaxy plugin.

    Sets up fallaxy and pulp (ansible-galaxy) servers for tests.

    The fallaxy source itself resides at: https://github.com/ansible/fallaxy-test-container
    The pulp source itself resides at: https://github.com/pulp/pulp-oci-images
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(GalaxyProvider, self).__init__(args)

        self.fallaxy = os.environ.get(
            'ANSIBLE_FALLAXY_CONTAINER',
            'quay.io/ansible/fallaxy-test-container:2.0.1'
        )
        self.pulp = os.environ.get(
            'ANSIBLE_PULP_CONTAINER',
            'docker.io/pulp/pulp-fedora31@sha256:71054f92fc9c986ba823d86b68631bafc84ae61b7832ce0be1f8e74423e56f64'
        )

        self.containers = []

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
        super(GalaxyProvider, self).setup()

        container_id = get_docker_container_id()

        if container_id:
            display.info('Running in docker container: %s' % container_id, verbosity=1)

        f_results = docker_inspect(self.args, 'fallaxy-stub')
        p_results = docker_inspect(self.args, 'pulp')

        if f_results and not f_results[0].get('State', {}).get('Running'):
            docker_rm(self.args, 'fallaxy-stub')
            f_results = []

        if p_results and not p_results[0].get('State', {}).get('Running'):
            docker_rm(self.args, 'pulp')
            p_results = []

        display.info('%s fallaxy-stub docker container.'
                     % ('Using the existing' if f_results else 'Starting a new'),
                     verbosity=1)

        fallaxy_port = 8080
        fallaxy_token = str(uuid.uuid4()).replace('-', '')

        if not f_results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(fallaxy_port),) * 2),
                ]

            docker_pull(self.args, self.fallaxy)

            docker_run(
                self.args,
                self.fallaxy,
                ['-d', '--name', 'fallaxy-stub', '-e', 'FALLAXY_TOKEN=%s' % fallaxy_token] + publish_ports,
            )
            self.containers.append('fallaxy-stub')

        if self.args.docker:
            fallaxy_host = 'fallaxy-stub'
        elif container_id:
            fallaxy_host = self._get_simulator_address('fallaxy-stub')
            display.info('Found Galaxy simulator container address: %s' % fallaxy_host, verbosity=1)
        else:
            fallaxy_host = 'localhost'

        self._set_cloud_config('FALLAXY_HOST', fallaxy_host)
        self._set_cloud_config('FALLAXY_PORT', str(fallaxy_port))
        self._set_cloud_config('FALLAXY_TOKEN', fallaxy_token)

        display.info('%s pulp docker container.'
                     % ('Using the existing' if p_results else 'Starting a new'),
                     verbosity=1)

        pulp_port = 80

        if not p_results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(fallaxy_port),) * 2),
                ]

            docker_pull(self.args, self.pulp)

            # Create the container, don't run it, we need to inject configs before it starts
            stdout, _dummy = docker_run(
                self.args,
                self.pulp,
                ['--name', 'pulp'] + publish_ports,
                create_only=True
            )

            pulp_id = stdout.strip()

            try:
                # Inject our settings.py file
                with tempfile.NamedTemporaryFile(delete=False) as settings:
                    settings.write(SETTINGS)
                docker_command(self.args, ['cp', settings.name, '%s:/etc/pulp/settings.py' % pulp_id])
            finally:
                os.unlink(settings.name)

            try:
                # Inject our settings.py file
                with tempfile.NamedTemporaryFile(delete=False) as admin_pass:
                    admin_pass.write(SET_ADMIN_PASSWORD)
                docker_command(self.args, ['cp', admin_pass.name, '%s:/etc/cont-init.d/111-postgres' % pulp_id])
            finally:
                os.unlink(admin_pass.name)

            # Start the container
            docker_start(self.args, 'pulp', [])

            self.containers.append('pulp')

        if self.args.docker:
            pulp_host = 'pulp'
        elif container_id:
            pulp_host = self._get_simulator_address('pulp')
            display.info('Found Galaxy simulator container address: %s' % pulp_host, verbosity=1)
        else:
            pulp_host = 'localhost'

        self._set_cloud_config('PULP_HOST', pulp_host)
        self._set_cloud_config('PULP_PORT', str(pulp_port))
        self._set_cloud_config('PULP_USER', 'admin')
        self._set_cloud_config('PULP_PASSWORD', 'password')

    def get_docker_run_options(self):
        """Get additional options needed when delegating tests to a container.

        :rtype: list[str]
        """
        return ['--link', 'fallaxy-stub', '--link', 'pulp']  # if self.managed else []

    def cleanup(self):
        """Clean up the resource and temporary configs files after tests."""
        for container_name in self.containers:
            docker_rm(self.args, container_name)

        super(GalaxyProvider, self).cleanup()

    def _get_simulator_address(self, container_name):
        results = docker_inspect(self.args, container_name)
        ipaddress = results[0]['NetworkSettings']['IPAddress']
        return ipaddress


class GalaxyEnvironment(CloudEnvironment):
    """Galaxy environment plugin.

    Updates integration test environment after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        fallaxy_token = self._get_cloud_config('FALLAXY_TOKEN')
        fallaxy_host = self._get_cloud_config('FALLAXY_HOST')
        fallaxy_port = self._get_cloud_config('FALLAXY_PORT')
        pulp_user = self._get_cloud_config('PULP_USER')
        pulp_password = self._get_cloud_config('PULP_PASSWORD')
        pulp_host = self._get_cloud_config('PULP_HOST')
        pulp_port = self._get_cloud_config('PULP_PORT')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                fallaxy_token=fallaxy_token,
                fallaxy_galaxy_server='http://%s:%s/api/' % (fallaxy_host, fallaxy_port),
                fallaxy_ah_server='http://%s:%s/api/automation-hub/' % (fallaxy_host, fallaxy_port),
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_v2_server='http://%s:%s/pulp_ansible/galaxy/ansible_ci/api/' % (pulp_host, pulp_port),
                pulp_v3_server='http://%s:%s/pulp_ansible/galaxy/ansible_ci/api/' % (pulp_host, pulp_port),
                pulp_api='http://%s:%s' % (pulp_host, pulp_port),
            ),
            env_vars=dict(
                FALLAXY_TOKEN=fallaxy_token,
                FALLAXY_GALAXY_SERVER='http://%s:%s/api/' % (fallaxy_host, fallaxy_port),
                FALLAXY_AH_SERVER='http://%s:%s/api/automation-hub/' % (fallaxy_host, fallaxy_port),
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_V2_SERVER='http://%s:%s/pulp_ansible/galaxy/ansible_ci/api/' % (pulp_host, pulp_port),
                PULP_V3_SERVER='http://%s:%s/pulp_ansible/galaxy/ansible_ci/api/' % (pulp_host, pulp_port),
            ),
        )
