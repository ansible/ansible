"""Galaxy (ansible-galaxy) plugin for integration tests."""
from __future__ import annotations

import os
import tempfile

from ....config import (
    IntegrationConfig,
)

from ....docker_util import (
    docker_cp_to,
    docker_exec,
)

from ....containers import (
    run_support_container,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


GALAXY_IMPORTER = b'''
[galaxy-importer]
ansible_local_tmp=~/.ansible/tmp
ansible_test_local_image=false
check_required_tags=false
check_runtime_yaml=false
check_changelog=false
infra_osd=false
local_image_docker=false
log_level_main=INFO
require_v1_or_greater=false
run_ansible_doc=false
run_ansible_lint=false
run_ansible_test=false
run_flake8=false
'''


class GalaxyProvider(CloudProvider):
    """
    Galaxy plugin. Sets up pulp (ansible-galaxy) servers for tests.
    The pulp source itself resides at: https://github.com/pulp/pulp-oci-images
    """

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.image = os.environ.get(
            'ANSIBLE_PULP_CONTAINER',
            'quay.io/pulp/galaxy:4.7.1'
        )

        self.uses_docker = True

    def setup(self) -> None:
        """Setup cloud resource before delegation and reg cleanup callback."""
        super().setup()

        name = 'galaxy-pulp'
        galaxy_port = 80

        ports = [
            galaxy_port,
        ]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            name,
            ports,
            aliases=[
                name,
            ],
            start=True,
            options=[
                '--env-file',
                os.path.join(
                    os.path.dirname(__file__),
                    'galaxy.env'
                ),
            ],
        )

        if not descriptor:
            return

        injected_files = {
            '/etc/galaxy-importer/galaxy-importer.cfg': GALAXY_IMPORTER,
        }
        for path, content in injected_files.items():
            with tempfile.NamedTemporaryFile() as temp_fd:
                temp_fd.write(content)
                temp_fd.flush()
                docker_exec(self.args, descriptor.container_id, ['mkdir', '-p', os.path.dirname(path)], True)
                docker_cp_to(self.args, descriptor.container_id, temp_fd.name, path)

        self._set_cloud_config('PULP_HOST', name)
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

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_api='http://%s:%s' % (pulp_host, galaxy_port),
                pulp_server='http://%s:%s/pulp_ansible/galaxy/' % (pulp_host, galaxy_port),
                galaxy_ng_server='http://%s:%s/api/galaxy/' % (pulp_host, galaxy_port),
            ),
            env_vars=dict(
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_SERVER='http://%s:%s/pulp_ansible/galaxy/api/' % (pulp_host, galaxy_port),
                GALAXY_NG_SERVER='http://%s:%s/api/galaxy/' % (pulp_host, galaxy_port),
            ),
        )
