"""HTTP Tester plugin for integration tests."""

from __future__ import annotations

import os

from ....util import (
    display,
    generate_password,
)

from ....config import (
    IntegrationConfig,
)

from ....containers import (
    run_support_container,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)

KRB5_PASSWORD_ENV = 'KRB5_PASSWORD'


class HttptesterProvider(CloudProvider):
    """HTTP Tester provider plugin. Sets up resources before delegation."""

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        self.image = os.environ.get('ANSIBLE_HTTP_TEST_CONTAINER', 'quay.io/ansible/http-test-container:3.5.0')

        self.uses_docker = True

    def setup(self) -> None:
        """Setup resources before delegation."""
        super().setup()

        ports = [
            80,
            88,
            443,
            444,
            749,
        ]

        aliases = [
            'ansible.http.tests',
            'sni1.ansible.http.tests',
            'fail.ansible.http.tests',
            'self-signed.ansible.http.tests',
        ]

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            'http-test-container',
            ports,
            aliases=aliases,
            env={
                KRB5_PASSWORD_ENV: generate_password(),
            },
        )

        if not descriptor:
            return

        # Read the password from the container environment.
        # This allows the tests to work when reusing an existing container.
        # The password is marked as sensitive, since it may differ from the one we generated.
        krb5_password = descriptor.details.container.env_dict()[KRB5_PASSWORD_ENV]
        display.sensitive.add(krb5_password)

        self._set_cloud_config(KRB5_PASSWORD_ENV, krb5_password)


class HttptesterEnvironment(CloudEnvironment):
    """HTTP Tester environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        return CloudEnvironmentConfig(
            env_vars=dict(
                HTTPTESTER='1',  # backwards compatibility for tests intended to work with or without HTTP Tester
                KRB5_PASSWORD=str(self._get_cloud_config(KRB5_PASSWORD_ENV)),
            )
        )
