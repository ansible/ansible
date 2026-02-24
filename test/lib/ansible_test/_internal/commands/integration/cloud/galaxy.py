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


GALAXY_HOST = 'galaxy'

# These settings must stay in sync with the galaxy_ng.env file in github.com/ansible/galaxy-ng-test-container
SETTINGS = {
    "GNUPGHOME": "/etc/pulp/gnupg/",
    "DJANGO_SUPERUSER_USERNAME": "admin",
    "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
    "DJANGO_SUPERUSER_PASSWORD": "admin",
    "POSTGRES_USER": "galaxy_ng",
    "POSTGRES_PASSWORD": "galaxy_ng",
    "POSTGRES_DB": "galaxy_ng",
    "PULP_CACHE_ENABLED": "false",
    "PULP_ANALYTICS": "false",
    "PULP_DATABASES__default__ENGINE": "django.db.backends.postgresql",
    "PULP_DATABASES__default__NAME": "galaxy_ng",
    "PULP_DATABASES__default__USER": "galaxy_ng",
    "PULP_DATABASES__default__PASSWORD": "galaxy_ng",
    "PULP_DATABASES__default__HOST": "postgres",
    "PULP_DATABASES__default__PORT": "5432",
    "PULP_DEBUG": "0",
    "PULP_GALAXY_DEPLOYMENT_MODE": "standalone",
    "PULP_DEFAULT_FILE_STORAGE": "pulpcore.app.models.storage.FileSystem",
    "PULP_REDIRECT_TO_OBJECT_STORAGE": "false",
    "PULP_GALAXY_API_PATH_PREFIX": "/api/galaxy/",
    "PULP_CONTENT_PATH_PREFIX": "/pulp/content/",
    "PULP_ANSIBLE_API_HOSTNAME": f"http://{GALAXY_HOST}:8000",
    "PULP_ANSIBLE_CONTENT_HOSTNAME": f"http://{GALAXY_HOST}:24816",
    "PULP_CONTENT_ORIGIN": f"http://{GALAXY_HOST}:24816",
    "PULP_CSRF_TRUSTED_ORIGINS": [f'http://{GALAXY_HOST}'],
    "PULP_GALAXY_AUTO_SIGN_COLLECTIONS": "false",
    "PULP_GALAXY_REQUIRE_CONTENT_APPROVAL": "false",
    "PULP_GALAXY_REQUIRE_SIGNATURE_FOR_APPROVAL": "false",
    "PULP_GALAXY_COLLECTION_SIGNING_SERVICE": "ansible-default",
    "PULP_GALAXY_CONTAINER_SIGNING_SERVICE": "container-default",
    "PULP_TOKEN_AUTH_DISABLED": "false",
    "PULP_TOKEN_SERVER": f"http://{GALAXY_HOST}/token/",
    "PULP_TOKEN_SIGNATURE_ALGORITHM": "ES256",
    "PULP_PUBLIC_KEY_PATH": "/src/galaxy_ng/dev/common/container_auth_public_key.pem",
    "PULP_PRIVATE_KEY_PATH": "/src/galaxy_ng/dev/common/container_auth_private_key.pem",
    "PULP_GALAXY_AUTHENTICATION_CLASSES": [
        'galaxy_ng.app.auth.session.SessionAuthentication',
        'ansible_base.jwt_consumer.hub.auth.HubJWTAuth',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    "PULP_ANSIBLE_BASE_JWT_VALIDATE_CERT": "false",
    "PULP_ANSIBLE_BASE_JWT_KEY": f"http://{GALAXY_HOST}",
    "PULP_GALAXY_FEATURE_FLAGS__external_authentication": "true",
    "PULP_ALLOW_LOCAL_RESOURCE_MANAGEMENT": "false",
    "PULP_ANSIBLE_BASE_ROLES_REQUIRE_VIEW": "false",
    "PULP_RESOURCE_SERVER_SYNC_ENABLED": "false",
    "LOCK_REQUIREMENTS": "0",
    "DEV_SOURCE_PATH": "",
    "ENABLE_DEBUGPY": ""
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
    Galaxy plugin. Sets up ansible-galaxy servers for tests.
    """

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.uses_docker = True
        self.galaxy_image = os.getenv(
            'ANSIBLE_GALAXY_CONTAINER',
            'ghcr.io/ansible/galaxy-ng-test-container:26.03.0'
        )
        self.postgres_image = os.getenv(
            'ANSIBLE_POSTGRES_CONTAINER',
            'quay.io/lib/postgres:13'
        )
        self.amanda_image = os.getenv(
            'ANSIBLE_AMANDA_CONTAINER',
            'ghcr.io/sivel/amanda@sha256:f704fe6f062b8ada59ae6553a70d2175295d068d56f544875980581b7df9c16d'
        )

    def setup(self) -> None:
        """Setup cloud resource before delegation and reg cleanup callback."""
        super().setup()

        gdata = run_support_container(self.args, self.platform, self.galaxy_image, 'galaxy-data', [0], start=False)
        if not gdata:
            return

        amanda = run_support_container(
            self.args,
            self.platform,
            self.amanda_image,
            'amanda',
            [8001],
            aliases=['amanda'],
            options=[
                '--volumes-from', gdata.container_id,
            ],
            cmd=['-port', '8001', '-publish'],
        )
        if not amanda:
            return

        postgres = run_support_container(
            self.args,
            self.platform,
            self.postgres_image,
            'galaxy-postgres',
            [5432],
            aliases=['postgres'],
            options=[
                '--volumes-from', gdata.container_id,
            ],
        )
        if not postgres:
            return

        with tempfile.NamedTemporaryFile(mode='w+') as env_fd:
            settings = '\n'.join(
                f'{key}={value}' for key, value in SETTINGS.items()
            )
            env_fd.write(settings)
            env_fd.flush()
            display.info(f'>>> galaxy_ng Configuration\n{settings}', verbosity=3)
            galaxy_ng = run_support_container(
                self.args,
                self.platform,
                self.galaxy_image,
                'galaxy_ng',
                [8000, 24816],
                aliases=['galaxy'],
                start=True,
                options=[
                    '--env-file', env_fd.name,
                    '--add-host', f'postgres:{postgres.details.container_ip}',
                ],
                cmd=[
                    '/bin/sh', '-c',
                    '(start-api &); (start-content-app &); start-worker;'
                ],
            )
        if not galaxy_ng:
            return

        injected_files = [
            ('/etc/galaxy-importer/galaxy-importer.cfg', GALAXY_IMPORTER, 'galaxy-importer'),
        ]
        for path, content, friendly_name in injected_files:
            with tempfile.NamedTemporaryFile() as temp_fd:
                temp_fd.write(content)
                temp_fd.flush()
                display.info(f'>>> {friendly_name} Configuration\n{to_text(content)}', verbosity=3)
                docker_exec(self.args, galaxy_ng.container_id, ['mkdir', '-p', os.path.dirname(path)], True, options=['-u', 'root'])
                docker_cp_to(self.args, galaxy_ng.container_id, temp_fd.name, path)
                docker_exec(self.args, galaxy_ng.container_id, ['chown', 'galaxy:galaxy', path], True, options=['-u', 'root'])

        self._set_cloud_config('GALAXY_HOST', GALAXY_HOST)
        self._set_cloud_config('GALAXY_USER', 'admin')
        self._set_cloud_config('GALAXY_PASSWORD', 'admin')
        self._set_cloud_config('AMANDA_HOST', 'amanda')


class GalaxyEnvironment(CloudEnvironment):
    """Galaxy environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        galaxy_user = str(self._get_cloud_config('GALAXY_USER'))
        galaxy_password = str(self._get_cloud_config('GALAXY_PASSWORD'))
        galaxy_host = self._get_cloud_config('GALAXY_HOST')
        amanda_host = self._get_cloud_config('AMANDA_HOST')

        return CloudEnvironmentConfig(
            ansible_vars=dict(
                galaxy_user=galaxy_user,
                galaxy_password=galaxy_password,
                galaxy_ng_server=f'http://{galaxy_host}:8000/api/galaxy',
                amanda=f'http://{amanda_host}:8001',
            ),
            env_vars=dict(
                GALAXY_USER=galaxy_user,
                GALAXY_PASSWORD=galaxy_password,
                GALAXY_NG_SERVER=f'http://{galaxy_host}:8000/api/galaxy',
                AMANDA=f'http://{amanda_host}:8001',
            ),
        )
