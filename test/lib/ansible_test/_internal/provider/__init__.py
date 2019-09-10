"""Provider (plugin) infrastructure for ansible-test."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import abc
import os

from .. import types as t

from ..util import (
    ABC,
    ApplicationError,
    get_subclasses,
)


try:
    TPathProvider = t.TypeVar('TPathProvider', bound='PathProvider')
except AttributeError:
    TPathProvider = None  # pylint: disable=invalid-name


def get_path_provider_classes(provider_type):  # type: (t.Type[TPathProvider]) -> t.List[t.Type[TPathProvider]]
    """Return a list of path provider classes of the given type."""
    return sorted(get_subclasses(provider_type), key=lambda c: (c.priority, c.__name__))


def find_path_provider(provider_type,  # type: t.Type[TPathProvider],
                       provider_classes,  # type:  t.List[t.Type[TPathProvider]]
                       path,  # type: str
                       walk,  # type: bool
                       ):  # type: (...) -> TPathProvider
    """Return the first found path provider of the given type for the given path."""
    sequences = sorted(set(pc.sequence for pc in provider_classes if pc.sequence > 0))

    for sequence in sequences:
        candidate_path = path
        tier_classes = [pc for pc in provider_classes if pc.sequence == sequence]

        while True:
            for provider_class in tier_classes:
                if provider_class.is_content_root(candidate_path):
                    return provider_class(candidate_path)

            if not walk:
                break

            parent_path = os.path.dirname(candidate_path)

            if parent_path == candidate_path:
                break

            candidate_path = parent_path

    raise ProviderNotFoundForPath(provider_type, path)


class ProviderNotFoundForPath(ApplicationError):
    """Exception generated when a path based provider cannot be found for a given path."""
    def __init__(self, provider_type, path):  # type: (t.Type, str) -> None
        super(ProviderNotFoundForPath, self).__init__('No %s found for path: %s' % (provider_type.__name__, path))

        self.provider_type = provider_type
        self.path = path


class PathProvider(ABC):
    """Base class for provider plugins that are path based."""
    sequence = 500
    priority = 500

    def __init__(self, root):  # type: (str) -> None
        self.root = root

    @staticmethod
    @abc.abstractmethod
    def is_content_root(path):  # type: (str) -> bool
        """Return True if the given path is a content root for this provider."""
