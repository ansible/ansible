"""ACME plugin for integration tests."""

from __future__ import annotations

import collections.abc as c
import os
import random
import time
import typing as t

from ....config import (
    IntegrationConfig,
)

from ....containers import (
    run_support_container,
)

from ....http import (
    HttpClient,
)

from ....util import (
    ApplicationError,
    display,
)

from ....util_common import (
    CommonConfig,
)

from . import (
    CloudEnvironment,
    CloudEnvironmentConfig,
    CloudProvider,
)


def wait_for_url(
    args: CommonConfig,
    url: str,
    *,
    sleep: int,
    tries: int,
    check: t.Optional[c.Callable[[int, str], bool]] = None,
) -> tuple[int, str]:
    """Wait for the specified URL to become available and return its HTTP status code and contents."""
    display.info(f"Waiting for URL {url!r}", verbosity=1)

    if not check:
        def check(status: int, content: str) -> bool:  # pylint: disable=unused-argument
            return 200 <= status < 300

    client = HttpClient(args)
    for _iteration in range(1, tries):
        if _iteration > 1:
            time.sleep(sleep)

        try:
            response = client.get(url)
            status, content = response.status_code, response.response
        except Exception as exc:  # pylint: disable=broad-exception-caught
            status, content = -1, f"Error: {exc}"
            continue

        display.info(f"GET {url} -> {status}: {content!r}", verbosity=2)

        if check(status, content):
            return status, content

    raise ApplicationError(f"Timeout waiting for URL {url!r}; last status was {status} and last content was {content!r}")


class ACMEProvider(CloudProvider):
    """ACME plugin. Sets up cloud resources for tests."""

    def __init__(self, args: IntegrationConfig) -> None:
        super().__init__(args)

        # The simulator must be pinned to a specific version to guarantee CI passes with the version used.
        self.image = os.getenv(
            'ANSIBLE_ACME_CONTAINER',
            'quay.io/ansible/acme-test-container:2.4.1',
        )

        self.uses_docker = True

    def setup(self) -> None:
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super().setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def _setup_dynamic(self) -> None:
        """Create a ACME test container using docker."""
        ports = [
            5000,  # control port for flask app in container
            14000,  # Pebble ACME CA
        ]

        hostname = 'pebble'

        descriptor = run_support_container(
            self.args,
            self.platform,
            self.image,
            'acme-simulator',
            ports,
            aliases=[hostname],
        )

        if not descriptor:
            return

        if not self.args.explain:
            def check(status: int, content: str) -> bool:
                return 200 <= status < 300 and content.startswith("-----BEGIN CERTIFICATE-----")

            if 5000 in descriptor.details.published_ports:
                our_hostname = f"localhost:{descriptor.details.published_ports[5000]}"
            else:
                our_hostname = f"{descriptor.details.container_ip}:5000"
            dummy, root_ca = wait_for_url(self.args, f"http://{our_hostname}/root-certificate-for-acme-endpoint", sleep=1, tries=30, check=check)

            self._set_cloud_config('acme_endpoint_root_ca_certificate_content', root_ca)
            rnd = random.randbytes(6).hex()
            self._set_cloud_config('acme_endpoint_root_ca_certificate_filename', f'/tmp/acme-simulator-ca-cert-{rnd}.pem')

        self._set_cloud_config('acme_host', hostname)

    def _setup_static(self) -> None:
        raise NotImplementedError()


class ACMEEnvironment(CloudEnvironment):
    """ACME environment plugin. Updates integration test environment after delegation."""

    def get_environment_config(self) -> CloudEnvironmentConfig:
        """Return environment configuration for use in the test environment after delegation."""
        ca_path_content = self._get_cloud_config('acme_endpoint_root_ca_certificate_content')
        ca_path = self._get_cloud_config('acme_endpoint_root_ca_certificate_filename')
        acme_host = self._get_cloud_config('acme_host')
        acme_directory = f'https://{acme_host}:14000/dir'

        ansible_vars = dict(
            acme_endpoint_root_ca_certificate_content=ca_path_content,
            acme_endpoint_root_ca_certificate_filename=ca_path,
            acme_host=acme_host,
            acme_directory=acme_directory,
        )

        return CloudEnvironmentConfig(
            ansible_vars=ansible_vars,
            module_defaults={
                'group/acme': {
                    'ca_path': ca_path,
                    'acme_version': 2,
                    'acme_directory': acme_directory,
                },
            },
        )
