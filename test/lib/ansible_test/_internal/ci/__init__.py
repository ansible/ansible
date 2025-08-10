"""Support code for CI environments."""

from __future__ import annotations

import abc
import dataclasses
import datetime
import json
import pathlib
import tempfile
import typing as t

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


@dataclasses.dataclass(frozen=True, kw_only=True)
class AuthContext:
    """Information about the request to which authentication will be applied."""

    stage: str
    provider: str
    request_id: str


class AuthHelper:
    """Authentication helper."""

    NAMESPACE: t.ClassVar = 'ci@core.ansible.com'

    def __init__(self, key_file: pathlib.Path) -> None:
        self.private_key_file = pathlib.Path(str(key_file).removesuffix('.pub'))
        self.public_key_file = pathlib.Path(f'{self.private_key_file}.pub')

    def sign_request(self, request: dict[str, object], context: AuthContext) -> None:
        """Sign the given auth request using the provided context."""
        request.update(
            stage=context.stage,
            provider=context.provider,
            request_id=context.request_id,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0).isoformat(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = pathlib.Path(temp_dir) / 'auth.json'
            payload_path.write_text(json.dumps(request, sort_keys=True))

            cmd = ['ssh-keygen', '-q', '-Y', 'sign', '-f', str(self.private_key_file), '-n', self.NAMESPACE, str(payload_path)]
            raw_command(cmd, capture=False, interactive=True)

            signature_path = pathlib.Path(f'{payload_path}.sig')
            signature = signature_path.read_text()

        request.update(signature=signature)


class GeneratingAuthHelper(AuthHelper, metaclass=abc.ABCMeta):
    """Authentication helper which generates a key pair on demand."""

    def __init__(self) -> None:
        super().__init__(pathlib.Path('~/.ansible/test/ansible-core-ci').expanduser())

    def sign_request(self, request: dict[str, object], context: AuthContext) -> None:
        if not self.private_key_file.exists():
            self.generate_key_pair()

        super().sign_request(request, context)

    def generate_key_pair(self) -> None:
        """Generate key pair."""
        self.private_key_file.parent.mkdir(parents=True, exist_ok=True)

        raw_command(['ssh-keygen', '-q', '-f', str(self.private_key_file), '-N', ''], capture=True)


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
    def prepare_core_ci_request(self, config: dict[str, object], context: AuthContext) -> dict[str, object]:
        """Prepare an Ansible Core CI request using the given config and context."""

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
