"""Support code for CI environments."""
from __future__ import annotations

import abc
import base64
import json
import os
import tempfile
import typing as t

from ..encoding import (
    to_bytes,
    to_text,
)

from ..io import (
    read_text_file,
    write_text_file,
)

from ..config import (
    CommonConfig,
    TestConfig,
)

from ..util import (
    ApplicationError,
    display,
    get_subclasses,
    import_plugins,
    raw_command,
    cache,
)


class ChangeDetectionNotSupported(ApplicationError):
    """Exception for cases where change detection is not supported."""


class CIProvider(metaclass=abc.ABCMeta):
    """Base class for CI provider plugins."""

    priority = 500

    @staticmethod
    @abc.abstractmethod
    def is_supported() -> bool:
        """Return True if this provider is supported in the current running environment."""

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """Return a unique code representing this provider."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return descriptive name for this provider."""

    @abc.abstractmethod
    def generate_resource_prefix(self) -> str:
        """Return a resource prefix specific to this CI provider."""

    @abc.abstractmethod
    def get_base_commit(self, args: CommonConfig) -> str:
        """Return the base commit or an empty string."""

    @abc.abstractmethod
    def detect_changes(self, args: TestConfig) -> t.Optional[list[str]]:
        """Initialize change detection."""

    @abc.abstractmethod
    def supports_core_ci_auth(self) -> bool:
        """Return True if Ansible Core CI is supported."""

    @abc.abstractmethod
    def prepare_core_ci_auth(self) -> dict[str, t.Any]:
        """Return authentication details for Ansible Core CI."""

    @abc.abstractmethod
    def get_git_details(self, args: CommonConfig) -> t.Optional[dict[str, t.Any]]:
        """Return details about git in the current environment."""


@cache
def get_ci_provider() -> CIProvider:
    """Return a CI provider instance for the current environment."""
    provider = None

    import_plugins('ci')

    candidates = sorted(get_subclasses(CIProvider), key=lambda subclass: (subclass.priority, subclass.__name__))

    for candidate in candidates:
        if candidate.is_supported():
            provider = candidate()
            break

    if provider.code:
        display.info('Detected CI provider: %s' % provider.name)

    return provider


class AuthHelper(metaclass=abc.ABCMeta):
    """Public key based authentication helper for Ansible Core CI."""

    def sign_request(self, request: dict[str, t.Any]) -> None:
        """Sign the given auth request and make the public key available."""
        payload_bytes = to_bytes(json.dumps(request, sort_keys=True))
        signature_raw_bytes = self.sign_bytes(payload_bytes)
        signature = to_text(base64.b64encode(signature_raw_bytes))

        request.update(signature=signature)

    def initialize_private_key(self) -> str:
        """
        Initialize and publish a new key pair (if needed) and return the private key.
        The private key is cached across ansible-test invocations, so it is only generated and published once per CI job.
        """
        path = os.path.expanduser('~/.ansible-core-ci-private.key')

        if os.path.exists(to_bytes(path)):
            private_key_pem = read_text_file(path)
        else:
            private_key_pem = self.generate_private_key()
            write_text_file(path, private_key_pem)

        return private_key_pem

    @abc.abstractmethod
    def sign_bytes(self, payload_bytes: bytes) -> bytes:
        """Sign the given payload and return the signature, initializing a new key pair if required."""

    @abc.abstractmethod
    def publish_public_key(self, public_key_pem: str) -> None:
        """Publish the given public key."""

    @abc.abstractmethod
    def generate_private_key(self) -> str:
        """Generate a new key pair, publishing the public key and returning the private key."""


class CryptographyAuthHelper(AuthHelper, metaclass=abc.ABCMeta):
    """Cryptography based public key based authentication helper for Ansible Core CI."""

    def sign_bytes(self, payload_bytes: bytes) -> bytes:
        """Sign the given payload and return the signature, initializing a new key pair if required."""
        # import cryptography here to avoid overhead and failures in environments which do not use/provide it
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        private_key_pem = self.initialize_private_key()
        private_key = load_pem_private_key(to_bytes(private_key_pem), None, default_backend())

        assert isinstance(private_key, ec.EllipticCurvePrivateKey)

        signature_raw_bytes = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))

        return signature_raw_bytes

    def generate_private_key(self) -> str:
        """Generate a new key pair, publishing the public key and returning the private key."""
        # import cryptography here to avoid overhead and failures in environments which do not use/provide it
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
        public_key = private_key.public_key()

        private_key_pem = to_text(private_key.private_bytes(  # type: ignore[attr-defined]  # documented method, but missing from type stubs
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))

        public_key_pem = to_text(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))

        self.publish_public_key(public_key_pem)

        return private_key_pem


class OpenSSLAuthHelper(AuthHelper, metaclass=abc.ABCMeta):
    """OpenSSL based public key based authentication helper for Ansible Core CI."""

    def sign_bytes(self, payload_bytes: bytes) -> bytes:
        """Sign the given payload and return the signature, initializing a new key pair if required."""
        private_key_pem = self.initialize_private_key()

        with tempfile.NamedTemporaryFile() as private_key_file:
            private_key_file.write(to_bytes(private_key_pem))
            private_key_file.flush()

            with tempfile.NamedTemporaryFile() as payload_file:
                payload_file.write(payload_bytes)
                payload_file.flush()

                with tempfile.NamedTemporaryFile() as signature_file:
                    raw_command(['openssl', 'dgst', '-sha256', '-sign', private_key_file.name, '-out', signature_file.name, payload_file.name], capture=True)
                    signature_raw_bytes = signature_file.read()

        return signature_raw_bytes

    def generate_private_key(self) -> str:
        """Generate a new key pair, publishing the public key and returning the private key."""
        private_key_pem = raw_command(['openssl', 'ecparam', '-genkey', '-name', 'secp384r1', '-noout'], capture=True)[0]
        public_key_pem = raw_command(['openssl', 'ec', '-pubout'], data=private_key_pem, capture=True)[0]

        self.publish_public_key(public_key_pem)

        return private_key_pem
