"""Support code for CI environments."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import base64
import json
import os
import subprocess  # using subprocess directly since we're interested in working with bytes instead of text
import tempfile


from .. import types as t

from ..io import (
    read_binary_file,
    write_binary_file,
)

from ..config import (
    CommonConfig,
    TestConfig,
)

from ..util import (
    ABC,
    ApplicationError,
    display,
    get_subclasses,
    import_plugins,
)


class ChangeDetectionNotSupported(ApplicationError):
    """Exception for cases where change detection is not supported."""


class AuthContext:
    """Context information required for Ansible Core CI authentication."""
    def __init__(self):  # type: () -> None
        self.region = None  # type: t.Optional[str]


class CIProvider(ABC):
    """Base class for CI provider plugins."""
    priority = 500

    @staticmethod
    @abc.abstractmethod
    def is_supported():  # type: () -> bool
        """Return True if this provider is supported in the current running environment."""

    @property
    @abc.abstractmethod
    def code(self):  # type: () -> str
        """Return a unique code representing this provider."""

    @property
    @abc.abstractmethod
    def name(self):  # type: () -> str
        """Return descriptive name for this provider."""

    @abc.abstractmethod
    def generate_resource_prefix(self):  # type: () -> str
        """Return a resource prefix specific to this CI provider."""

    @abc.abstractmethod
    def get_base_branch(self):  # type: () -> str
        """Return the base branch or an empty string."""

    @abc.abstractmethod
    def detect_changes(self, args):  # type: (TestConfig) -> t.Optional[t.List[str]]
        """Initialize change detection."""

    @abc.abstractmethod
    def supports_core_ci_auth(self, context):  # type: (AuthContext) -> bool
        """Return True if Ansible Core CI is supported."""

    @abc.abstractmethod
    def prepare_core_ci_auth(self, context):  # type: (AuthContext) -> t.Dict[str, t.Any]
        """Return authentication details for Ansible Core CI."""

    @abc.abstractmethod
    def get_git_details(self, args):  # type: (CommonConfig) -> t.Optional[t.Dict[str, t.Any]]
        """Return details about git in the current environment."""


def get_ci_provider():  # type: () -> CIProvider
    """Return a CI provider instance for the current environment."""
    try:
        return get_ci_provider.provider
    except AttributeError:
        pass

    provider = None

    import_plugins('ci')

    candidates = sorted(get_subclasses(CIProvider), key=lambda c: (c.priority, c.__name__))

    for candidate in candidates:
        if candidate.is_supported():
            provider = candidate()
            break

    if provider.code:
        display.info('Detected CI provider: %s' % provider.name)

    get_ci_provider.provider = provider

    return provider


class AuthHelper(ABC):
    """Public key based authentication helper for Ansible Core CI."""
    def sign_request(self, request):  # type: (t.Dict[str, t.Any]) -> None
        """Sign the given auth request and make the public key available."""
        payload_bytes = json.dumps(request, sort_keys=True).encode()
        signature_base64_string = self.sign_bytes(payload_bytes)

        request.update(signature=signature_base64_string)

    def initialize_private_key(self):  # type: () -> bytes
        """
        Initialize and publish a new key pair (if needed) and return the private key.
        The private key is cached across ansible-test invocations so it is only generated and published once per CI job.
        """
        path = os.path.expanduser('~/.ansible-core-ci-private.key')

        if os.path.exists(path):
            private_key_pem_bytes = read_binary_file(path)
        else:
            private_key_pem_bytes = self.generate_private_key()
            write_binary_file(path, private_key_pem_bytes)

        return private_key_pem_bytes

    @abc.abstractmethod
    def sign_bytes(self, payload_bytes):  # type: (bytes) -> str
        """
        Generate a private key and then sign the given bytes.
        Returns the PEM public key bytes and the base64 encoded signature string.
        """

    @abc.abstractmethod
    def publish_public_key(self, public_key_pem_bytes):
        """Publish the given public key."""

    @abc.abstractmethod
    def generate_private_key(self):  # type: () -> bytes
        """Generate a new key pair, publishing the public key and returning the private key."""


class OpenSSLAuthHelper(AuthHelper, ABC):  # pylint: disable=abstract-method
    """OpenSSL based public key based authentication helper for Ansible Core CI."""
    def sign_bytes(self, payload_bytes):  # type: (bytes) -> str
        """
        Generate a private key and then sign the given bytes.
        Returns the PEM public key bytes and the base64 encoded signature string.
        """
        private_key_pem_bytes = self.initialize_private_key()

        with open(os.devnull, 'wb') as devnull:
            with tempfile.NamedTemporaryFile() as private_key_file:
                private_key_file.write(private_key_pem_bytes)
                private_key_file.flush()

                with tempfile.NamedTemporaryFile() as payload_file:
                    payload_file.write(payload_bytes)
                    payload_file.flush()

                    signature_bytes = subprocess.check_output(['openssl', 'dgst', '-sha256', '-sign', private_key_file.name, payload_file.name], stderr=devnull)

        signature_base64_string = base64.b64encode(signature_bytes).decode()

        return signature_base64_string

    def generate_private_key(self):  # type: () -> bytes
        """Generate a new key pair, publishing the public key and returning the private key."""
        with open(os.devnull, 'wb') as devnull:
            private_key_pem_bytes = subprocess.check_output(['openssl', 'ecparam', '-genkey', '-name', 'secp384r1', '-noout'], stderr=devnull)

            openssl = subprocess.Popen(['openssl', 'ec', '-pubout'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=devnull)
            public_key_pem_bytes = openssl.communicate(private_key_pem_bytes)[0]

        self.publish_public_key(public_key_pem_bytes)

        return private_key_pem_bytes
