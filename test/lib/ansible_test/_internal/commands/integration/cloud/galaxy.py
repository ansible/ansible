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

from ....encoding import (
    to_text,
)

from ....util import (
    display,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


GALAXY_HOST_NAME = 'galaxy-pulp'
SETTINGS = {
    'PULP_CONTENT_ORIGIN': f'http://{GALAXY_HOST_NAME}',
    'PULP_ANSIBLE_API_HOSTNAME': f'http://{GALAXY_HOST_NAME}',
    'PULP_GALAXY_API_PATH_PREFIX': '/api/galaxy/',
    # These paths are unique to the container image which has an nginx location for /pulp/content to route
    # requests to the content backend
    'PULP_ANSIBLE_CONTENT_HOSTNAME': f'http://{GALAXY_HOST_NAME}/pulp/content/api/galaxy/v3/artifacts/collections/',
    'PULP_CONTENT_PATH_PREFIX': '/pulp/content/api/galaxy/v3/artifacts/collections/',
    'PULP_GALAXY_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'django.contrib.auth.backends.ModelBackend',
    ],
    # This should probably be false see https://issues.redhat.com/browse/AAH-2328
    'PULP_GALAXY_REQUIRE_CONTENT_APPROVAL': 'true',
    'PULP_GALAXY_DEPLOYMENT_MODE': 'standalone',
    'PULP_GALAXY_AUTO_SIGN_COLLECTIONS': 'false',
    'PULP_GALAXY_COLLECTION_SIGNING_SERVICE': 'ansible-default',
    'PULP_RH_ENTITLEMENT_REQUIRED': 'insights',
    'PULP_TOKEN_AUTH_DISABLED': 'false',
    'PULP_TOKEN_SERVER': f'http://{GALAXY_HOST_NAME}/token/',
    'PULP_TOKEN_SIGNATURE_ALGORITHM': 'ES256',
    'PULP_PUBLIC_KEY_PATH': '/src/galaxy_ng/dev/common/container_auth_public_key.pem',
    'PULP_PRIVATE_KEY_PATH': '/src/galaxy_ng/dev/common/container_auth_private_key.pem',
    'PULP_ANALYTICS': 'false',
    'PULP_GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_ACCESS': 'true',
    'PULP_GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_DOWNLOAD': 'true',
    'PULP_GALAXY_ENABLE_LEGACY_ROLES': 'true',
    'PULP_GALAXY_FEATURE_FLAGS__execution_environments': 'false',
    'PULP_SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/',
    'PULP_GALAXY_FEATURE_FLAGS__ai_deny_index': 'true',
    'PULP_DEFAULT_ADMIN_PASSWORD': 'password'
}


GALAXY_IMPORTER = b"""
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
""".strip()


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

        with tempfile.NamedTemporaryFile(mode='w+') as env_fd:
            settings = '\n'.join(
                f'{key}={value}' for key, value in SETTINGS.items()
            )
            env_fd.write(settings)
            env_fd.flush()
            display.info(f'>>> galaxy_ng Configuration\n{settings}', verbosity=3)
            descriptor = run_support_container(
                self.args,
                self.platform,
                self.image,
                GALAXY_HOST_NAME,
                [
                    80,
                ],
                aliases=[
                    GALAXY_HOST_NAME,
                ],
                start=True,
                options=[
                    '--env-file', env_fd.name,
                ],
            )

        if not descriptor:
            return

        injected_files = [
            ('/etc/galaxy-importer/galaxy-importer.cfg', GALAXY_IMPORTER, 'galaxy-importer'),
        ]
        for path, content, friendly_name in injected_files:
            with tempfile.NamedTemporaryFile() as temp_fd:
                temp_fd.write(content)
                temp_fd.flush()
                display.info(f'>>> {friendly_name} Configuration\n{to_text(content)}', verbosity=3)
                docker_exec(self.args, descriptor.container_id, ['mkdir', '-p', os.path.dirname(path)], True)
                docker_cp_to(self.args, descriptor.container_id, temp_fd.name, path)
                docker_exec(self.args, descriptor.container_id, ['chown', 'pulp:pulp', path], True)

        self._set_cloud_config('PULP_HOST', GALAXY_HOST_NAME)
        self._set_cloud_config('PULP_USER', 'admin')
        self._set_cloud_config('PULP_PASSWORD', 'password')


class GalaxyEnvironment(CloudEnvironment):
    """Galaxy environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        pulp_user = str(self._get_cloud_config('PULP_USER'))
        pulp_password = str(self._get_cloud_config('PULP_PASSWORD'))
        pulp_host = self._get_cloud_config('PULP_HOST')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                pulp_user=pulp_user,
                pulp_password=pulp_password,
                pulp_api=f'http://{pulp_host}',
                pulp_server=f'http://{pulp_host}/pulp_ansible/galaxy/',
                galaxy_ng_server=f'http://{pulp_host}/api/galaxy/',
            ),
            env_vars=dict(
                PULP_USER=pulp_user,
                PULP_PASSWORD=pulp_password,
                PULP_SERVER=f'http://{pulp_host}/pulp_ansible/galaxy/api/',
                GALAXY_NG_SERVER=f'http://{pulp_host}/api/galaxy/',
            ),
        )
