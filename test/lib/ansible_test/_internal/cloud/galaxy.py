"""Galaxy (ansible-galaxy) plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile

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

# This should not be needed once https://github.com/pulp/pulp-oci-images/pull/31 is merged in some shape or form.
# Recent galaxy_ng changes blocked access to the pulp endpoint through the normal listener so we need to ensure that
# gunicorn is bound to 0.0.0.0 and not 127.0.0.1.
RUN_OVERRIDE = b'''#!/usr/bin/execlineb -S0
foreground {
  export DJANGO_SETTINGS_MODULE pulpcore.app.settings
  export PULP_CONTENT_ORIGIN localhost
  /usr/local/bin/pulpcore-manager collectstatic --noinput --link
}
export DJANGO_SETTINGS_MODULE pulpcore.app.settings
export PULP_SETTINGS /etc/pulp/settings.py
/usr/local/bin/gunicorn pulpcore.app.wsgi:application --bind "0.0.0.0:24817" --access-logfile -
'''

# Part of the CI tests require us to remove all content which means the repository is removed in Pulp. Any existing
# namespaces defined in Galaxy NG need to be removed as well but no one is granted permissions to actually do that.
# Until another fix can be found we change the permissions from deny to allow. This sed calls changes the first
# occurrence to "allow" which is conveniently the delete operation for a namespace.
# https://github.com/ansible/galaxy_ng/blob/master/galaxy_ng/app/access_control/statements/standalone.py#L9-L11.
GALAXY_FIXES = b'''#!/usr/bin/execlineb -S0
foreground {
    sed -i "0,/\\"effect\\": \\"deny\\"/s//\\"effect\\": \\"allow\\"/" /usr/local/lib/python3.7/site-packages/galaxy_ng/app/access_control/statements/standalone.py
}'''


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
            'docker.io/pulp/pulp-galaxy-ng@sha256:b79a7be64eff86d8f58db9ca83ed4967bd8b4e45c99addb17a91d11926480cf1'
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

        p_results = docker_inspect(self.args, 'ansible-ci-pulp')

        if p_results and not p_results[0].get('State', {}).get('Running'):
            docker_rm(self.args, 'ansible-ci-pulp')
            p_results = []

        display.info('%s ansible-ci-pulp docker container.'
                     % ('Using the existing' if p_results else 'Starting a new'),
                     verbosity=1)

        pulp_port = 24817

        if not p_results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', '80:80',
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

            injected_files = {
                '/etc/pulp/settings.py': SETTINGS,
                '/etc/cont-init.d/111-postgres': SET_ADMIN_PASSWORD,
                '/etc/cont-init.d/000-ansible-test': GALAXY_FIXES,
                '/etc/services.d/pulpcore-api/run': RUN_OVERRIDE,
            }
            for path, content in injected_files.items():
                with tempfile.NamedTemporaryFile() as temp_fd:
                    temp_fd.write(content)
                    temp_fd.flush()
                    docker_command(self.args, ['cp', temp_fd.name, '%s:%s' % (pulp_id, path)])

            # Start the container
            docker_start(self.args, 'ansible-ci-pulp', [])

            self.containers.append('ansible-ci-pulp')

        if self.args.docker:
            pulp_host = 'ansible-ci-pulp'
        elif container_id:
            pulp_host = self._get_simulator_address('ansible-ci-pulp')
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
        return ['--link', 'ansible-ci-pulp']  # if self.managed else []

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
        pulp_user = self._get_cloud_config('PULP_USER')
        pulp_password = self._get_cloud_config('PULP_PASSWORD')
        pulp_host = self._get_cloud_config('PULP_HOST')
        pulp_port = self._get_cloud_config('PULP_PORT')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_v2_server='http://%s:%s/pulp_ansible/galaxy/published/api/' % (pulp_host, pulp_port),
                pulp_v3_server='http://%s:%s/pulp_ansible/galaxy/published/api/' % (pulp_host, pulp_port),
                pulp_api='http://%s:%s' % (pulp_host, pulp_port),
                galaxy_ng_server='http://%s:80/api/galaxy/' % (pulp_host,),
            ),
            env_vars=dict(
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_V2_SERVER='http://%s:%s/pulp_ansible/galaxy/published/api/' % (pulp_host, pulp_port),
                PULP_V3_SERVER='http://%s:%s/pulp_ansible/galaxy/published/api/' % (pulp_host, pulp_port),
                GALAXY_NG_SERVER='http://%s:80/api/galaxy/' % (pulp_host,),
            ),
        )
