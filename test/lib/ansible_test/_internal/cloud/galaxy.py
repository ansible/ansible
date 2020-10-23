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
    get_docker_hostname,
    get_docker_container_ip,
    get_docker_preferred_network_name,
    is_docker_user_defined_network,
)


# We add BasicAuthentication, to make the tasks that deal with
# direct API access easier to deal with across galaxy_ng and pulp
SETTINGS = b'''
CONTENT_ORIGIN = 'http://ansible-ci-pulp:80'
ANSIBLE_API_HOSTNAME = 'http://ansible-ci-pulp:80'
ANSIBLE_CONTENT_HOSTNAME = 'http://ansible-ci-pulp:80/pulp/content'
TOKEN_AUTH_DISABLED = True
GALAXY_REQUIRE_CONTENT_APPROVAL = False
GALAXY_AUTHENTICATION_CLASSES = [
    "rest_framework.authentication.SessionAuthentication",
    "rest_framework.authentication.TokenAuthentication",
    "rest_framework.authentication.BasicAuthentication",
]
'''

SET_ADMIN_PASSWORD = b'''#!/usr/bin/execlineb -S0
foreground {
  redirfd -w 1 /dev/null
  redirfd -w 2 /dev/null
  export DJANGO_SETTINGS_MODULE pulpcore.app.settings
  export PULP_CONTENT_ORIGIN localhost
  s6-setuidgid postgres
  if { /usr/local/bin/django-admin reset-admin-password --password password }
  if { /usr/local/bin/pulpcore-manager create-group system:partner-engineers --users admin }
}
'''


class GalaxyProvider(CloudProvider):
    """Galaxy plugin.

    Sets up pulp (ansible-galaxy) servers for tests.

    The pulp source itself resides at: https://github.com/pulp/pulp-oci-images
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(GalaxyProvider, self).__init__(args)

        self.pulp = os.environ.get(
            'ANSIBLE_PULP_CONTAINER',
            'docker.io/pulp/pulp-galaxy-ng@sha256:69b4c4cba4908539b56c5592f40d282f938dd1bdf4de5a81e0a8d04ac3e6e326'
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

        p_results = docker_inspect(self.args, 'ansible-ci-pulp')

        if p_results and not p_results[0].get('State', {}).get('Running'):
            docker_rm(self.args, 'ansible-ci-pulp')
            p_results = []

        display.info('%s ansible-ci-pulp docker container.'
                     % ('Using the existing' if p_results else 'Starting a new'),
                     verbosity=1)

        pulp_port = 80

        if not p_results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(pulp_port),) * 2),
                ]

            docker_pull(self.args, self.pulp)

            # Create the container, don't run it, we need to inject configs before it starts
            stdout, _dummy = docker_run(
                self.args,
                self.pulp,
                ['--name', 'ansible-ci-pulp'] + publish_ports,
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
            docker_start(self.args, 'ansible-ci-pulp', [])

            self.containers.append('ansible-ci-pulp')

        if self.args.docker:
            pulp_host = 'ansible-ci-pulp'
        elif container_id:
            pulp_host = self._get_simulator_address('ansible-ci-pulp')
            display.info('Found Galaxy simulator container address: %s' % pulp_host, verbosity=1)
        else:
            pulp_host = get_docker_hostname()

        self._set_cloud_config('PULP_HOST', pulp_host)
        self._set_cloud_config('PULP_PORT', str(pulp_port))
        self._set_cloud_config('PULP_USER', 'admin')
        self._set_cloud_config('PULP_PASSWORD', 'password')

    def get_docker_run_options(self):
        """Get additional options needed when delegating tests to a container.

        :rtype: list[str]
        """
        network = get_docker_preferred_network_name(self.args)

        if not is_docker_user_defined_network(network):
            return ['--link', 'ansible-ci-pulp']

        return []

    def cleanup(self):
        """Clean up the resource and temporary configs files after tests."""
        for container_name in self.containers:
            docker_rm(self.args, container_name)

        super(GalaxyProvider, self).cleanup()

    def _get_simulator_address(self, container_name):
        return get_docker_container_ip(self.args, container_name)


class GalaxyEnvironment(CloudEnvironment):
    """Galaxy environment plugin.

    Updates integration test environment after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        pulp_user = self._get_cloud_config('PULP_USER')
        pulp_password = self._get_cloud_config('PULP_PASSWORD')
        pulp_host = self._get_cloud_config('PULP_HOST')
        pulp_port = self._get_cloud_config('PULP_PORT')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_v2_server='http://%s:%s/pulp_ansible/galaxy/automation-hub/api/' % (pulp_host, pulp_port),
                pulp_v3_server='http://%s:%s/pulp_ansible/galaxy/automation-hub/api/' % (pulp_host, pulp_port),
                pulp_api='http://%s:%s' % (pulp_host, pulp_port),
                galaxy_ng_server='http://%s:%s/api/galaxy/' % (pulp_host, pulp_port),
            ),
            env_vars=dict(
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_V2_SERVER='http://%s:%s/pulp_ansible/galaxy/automation-hub/api/' % (pulp_host, pulp_port),
                PULP_V3_SERVER='http://%s:%s/pulp_ansible/galaxy/automation-hub/api/' % (pulp_host, pulp_port),
                GALAXY_NG_SERVER='http://%s:%s/api/galaxy/' % (pulp_host, pulp_port),
            ),
        )
