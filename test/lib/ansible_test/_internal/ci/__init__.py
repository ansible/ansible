"""Support code for CI environments."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc


from .. import types as t

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
