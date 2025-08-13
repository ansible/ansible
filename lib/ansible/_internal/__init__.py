from __future__ import annotations

import importlib
import typing as t

from ansible.module_utils import _internal
from ansible.module_utils._internal._json import _profiles


def get_controller_serialize_map() -> dict[type, t.Callable]:
    """
    Injected into module_utils code to augment serialization maps with controller-only types.
    This implementation replaces the no-op version in module_utils._internal in controller contexts.
    """
    from ansible._internal._templating import _lazy_containers
    from ansible.parsing.vault import EncryptedString

    return {
        _lazy_containers._AnsibleLazyTemplateDict: _profiles._JSONSerializationProfile.discard_tags,
        _lazy_containers._AnsibleLazyTemplateList: _profiles._JSONSerializationProfile.discard_tags,
        EncryptedString: str,  # preserves tags since this is an instance of EncryptedString; if tags should be discarded from str, another entry will handle it
    }


def import_controller_module(module_name: str, /) -> t.Any:
    """
    Injected into module_utils code to import and return the specified module.
    This implementation replaces the no-op version in module_utils._internal in controller contexts.
    """
    return importlib.import_module(module_name)


def experimental[T](obj: T) -> T:
    """
    Decorator for experimental types and methods outside the `_internal` package which accept or expose internal types.
    As with internal APIs, these are subject to change at any time without notice.
    """
    return obj


def setup() -> None:
    """No-op function to ensure that side-effect only imports of this module are not flagged/removed as 'unused'."""


# DTFIX-FUTURE: this is really fragile- disordered/incorrect imports (among other things) can mess it up. Consider a hosting-env-managed context
#  with an enum with at least Controller/Target/Unknown values, and possibly using lazy-init module shims or some other mechanism to allow controller-side
#  notification/augmentation of this kind of metadata.
_internal.get_controller_serialize_map = get_controller_serialize_map
_internal.import_controller_module = import_controller_module
_internal.is_controller = True
