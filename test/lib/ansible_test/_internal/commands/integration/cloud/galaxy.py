"""Galaxy (ansible-galaxy) plugin for integration tests."""
from __future__ import annotations

import os
import tempfile

from ....config import (
    IntegrationConfig,
)

from ....docker_util import (
    docker_cp_to,
)

from ....containers import (
    run_support_container,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
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

# There are 2 overrides here:
#   1. Change the gunicorn bind address from 127.0.0.1 to 0.0.0.0 now that Galaxy NG does not allow us to access the
#      Pulp API through it.
#   2. Grant access allowing us to DELETE a namespace in Galaxy NG. This is as CI deletes and recreates repos and
#      distributions in Pulp which now breaks the namespace in Galaxy NG. Recreating it is the "simple" fix to get it
#      working again.
# These may not be needed in the future, especially if 1 becomes configurable by an env var but for now they must be
# done.
OVERRIDES = b'''#!/usr/bin/execlineb -S0
foreground {
    sed -i "0,/\\"127.0.0.1:24817\\"/s//\\"0.0.0.0:24817\\"/" /etc/services.d/pulpcore-api/run
}

# This sed calls changes the first occurrence to "allow" which is conveniently the delete operation for a namespace.
# https://github.com/ansible/galaxy_ng/blob/master/galaxy_ng/app/access_control/statements/standalone.py#L9-L11.
backtick NG_PREFIX { python -c "import galaxy_ng; print(galaxy_ng.__path__[0], end='')" }
importas ng_prefix NG_PREFIX
foreground {
    sed -i "0,/\\"effect\\": \\"deny\\"/s//\\"effect\\": \\"allow\\"/" ${ng_prefix}/app/access_control/statements/standalone.py
}'''


class GalaxyProvider(CloudProvider):
    """
    Galaxy plugin. Sets up pulp (ansible-galaxy) servers for tests.
    The pulp source itself resides at: https://github.com/pulp/pulp-oci-images
    """

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        # Cannot use the latest container image as either galaxy_ng 4.2.0rc2 or pulp 0.5.0 has sporatic issues with
        # dropping published collections in CI. Try running the tests multiple times when updating. Will also need to
        # comment out the cache tests in 'test/integration/targets/ansible-galaxy-collection/tasks/install.yml' when
        # the newer update is available.
        self.pulp = os.environ.get(
            'ANSIBLE_PULP_CONTAINER',
            'quay.io/ansible/pulp-galaxy-ng:b79a7be64eff'
        )

        self.uses_docker = True

    def setup(self) -> None:
        """Setup cloud resource before delegation and reg cleanup callback."""
        super().setup()

        galaxy_port = 80
        pulp_host = 'ansible-ci-pulp'
        pulp_port = 24817

        ports = [
            galaxy_port,
            pulp_port,
        ]

        # Create the container, don't run it, we need to inject configs before it starts
        descriptor = run_support_container(
            self.args,
            self.platform,
            self.pulp,
            pulp_host,
            ports,
            start=False,
            allow_existing=True,
        )

        if not descriptor:
            return

        if not descriptor.running:
            pulp_id = descriptor.container_id

            injected_files = {
                '/etc/pulp/settings.py': SETTINGS,
                '/etc/cont-init.d/111-postgres': SET_ADMIN_PASSWORD,
                '/etc/cont-init.d/000-ansible-test-overrides': OVERRIDES,
            }
            for path, content in injected_files.items():
                with tempfile.NamedTemporaryFile() as temp_fd:
                    temp_fd.write(content)
                    temp_fd.flush()
                    docker_cp_to(self.args, pulp_id, temp_fd.name, path)

            descriptor.start(self.args)

        self._set_cloud_config('PULP_HOST', pulp_host)
        self._set_cloud_config('PULP_PORT', str(pulp_port))
        self._set_cloud_config('GALAXY_PORT', str(galaxy_port))
        self._set_cloud_config('PULP_USER', 'admin')
        self._set_cloud_config('PULP_PASSWORD', 'password')


class GalaxyEnvironment(CloudEnvironment):
    """Galaxy environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        pulp_user = str(self._get_cloud_config('PULP_USER'))
        pulp_password = str(self._get_cloud_config('PULP_PASSWORD'))
        pulp_host = self._get_cloud_config('PULP_HOST')
        galaxy_port = self._get_cloud_config('GALAXY_PORT')
        pulp_port = self._get_cloud_config('PULP_PORT')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_api='http://%s:%s' % (pulp_host, pulp_port),
                pulp_server='http://%s:%s/pulp_ansible/galaxy/' % (pulp_host, pulp_port),
                galaxy_ng_server='http://%s:%s/api/galaxy/' % (pulp_host, galaxy_port),
            ),
            env_vars=dict(
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_SERVER='http://%s:%s/pulp_ansible/galaxy/api/' % (pulp_host, pulp_port),
                GALAXY_NG_SERVER='http://%s:%s/api/galaxy/' % (pulp_host, galaxy_port),
            ),
        )
