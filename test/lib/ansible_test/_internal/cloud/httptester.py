"""HTTP Tester plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    display,
    generate_password,
)

from ..config import (
    IntegrationConfig,
)

from ..containers import (
    run_support_container,
)

KRB5_PASSWORD_ENV = 'KRB5_PASSWORD'


class HttptesterProvider(CloudProvider):
    """HTTP Tester provider plugin. Sets up resources before delegation."""
    def __init__(self, args):  # type: (IntegrationConfig) -> None
        super(HttptesterProvider, self).__init__(args)

        self.image = os.environ.get('ANSIBLE_HTTP_TEST_CONTAINER', 'quay.io/ansible/http-test-container:1.3.0')

        self.uses_docker = True

    def setup(self):  # type: () -> None
        """Setup resources before delegation."""
        super(HttptesterProvider, self).setup()

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
            start=True,
            allow_existing=True,
            cleanup=True,
            env={
                KRB5_PASSWORD_ENV: generate_password(),
            },
        )

        descriptor.register(self.args)

        # Read the password from the container environment.
        # This allows the tests to work when re-using an existing container.
        # The password is marked as sensitive, since it may differ from the one we generated.
        krb5_password = descriptor.details.container.env_dict()[KRB5_PASSWORD_ENV]
        display.sensitive.add(krb5_password)

        self._set_cloud_config(KRB5_PASSWORD_ENV, krb5_password)


class HttptesterEnvironment(CloudEnvironment):
    """HTTP Tester environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):  # type: () -> CloudEnvironmentConfig
        """Returns the cloud environment config."""
        return CloudEnvironmentConfig(
            env_vars=dict(
                HTTPTESTER='1',  # backwards compatibility for tests intended to work with or without HTTP Tester
                KRB5_PASSWORD=self._get_cloud_config(KRB5_PASSWORD_ENV),
            )
        )
