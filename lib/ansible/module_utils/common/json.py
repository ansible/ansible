from __future__ import annotations as _annotations

import enum as _enum
import json as _stdlib_json
import types as _types

from ansible.module_utils import _internal
from ansible.module_utils._internal import _json
from ansible.module_utils._internal._json import _legacy_encoder
from ansible.module_utils._internal._json import _profiles
from ansible.module_utils._internal._json._profiles import _tagless
from ansible.module_utils.common import warnings as _warnings


def __getattr__(name: str) -> object:
    """Handle dynamic module members which are or will be deprecated."""
    if name in ('AnsibleJSONEncoder', '_AnsibleJSONEncoder'):
        # deprecated: description='deprecate legacy encoder' core_version='2.23'
        # if not name.startswith('_'):  # avoid duplicate deprecation warning for imports from ajson
        #     _warnings.deprecate(
        #         msg="The `AnsibleJSONEncoder` type is deprecated.",
        #         version="2.27",
        #         help_text="Use a profile-based encoder instead.",  # DTFIX-FUTURE: improve this help text
        #     )

        return _get_legacy_encoder()

    if name in ('AnsibleJSONDecoder', '_AnsibleJSONDecoder'):
        # deprecated: description='deprecate legacy decoder' core_version='2.23'
        # if not name.startswith('_'):  # avoid duplicate deprecation warning for imports from ajson
        #     _warnings.deprecate(
        #         msg="The `AnsibleJSONDecoder` type is deprecated.",
        #         version="2.27",
        #         help_text="Use a profile-based decoder instead.",  # DTFIX-FUTURE: improve this help text
        #     )

        return _tagless.Decoder

    if name == 'json_dump':
        _warnings.deprecate(
            msg="The `json_dump` function is deprecated.",
            version="2.23",
            help_text="Use `json.dumps` with the appropriate `cls` instead.",
        )

        return _json_dump

    raise AttributeError(name)


def _get_legacy_encoder() -> type[_stdlib_json.JSONEncoder]:
    """Compatibility hack: previous module_utils AnsibleJSONEncoder impl did controller-side work, controller plugins require a more fully-featured impl."""
    if _internal.is_controller:
        return _internal.import_controller_module('ansible._internal._json._legacy_encoder').LegacyControllerJSONEncoder

    return _legacy_encoder.LegacyTargetJSONEncoder


def _json_dump(structure):
    """JSON dumping function maintained for temporary backward compatibility."""
    return _stdlib_json.dumps(structure, cls=_get_legacy_encoder(), sort_keys=True, indent=4)


class Direction(_enum.Enum):
    """Enumeration used to select a contextually-appropriate JSON profile for module messaging."""

    CONTROLLER_TO_MODULE = _enum.auto()
    """Encode/decode messages from the Ansible controller to an Ansible module."""
    MODULE_TO_CONTROLLER = _enum.auto()
    """Encode/decode messages from an Ansible module to the Ansible controller."""


def get_encoder(profile: str | _types.ModuleType, /) -> type[_stdlib_json.JSONEncoder]:
    """Return a `JSONEncoder` for the given `profile`."""
    return _json.get_encoder_decoder(profile, _profiles.AnsibleProfileJSONEncoder)


def get_decoder(profile: str | _types.ModuleType, /) -> type[_stdlib_json.JSONDecoder]:
    """Return a `JSONDecoder` for the given `profile`."""
    return _json.get_encoder_decoder(profile, _profiles.AnsibleProfileJSONDecoder)


def get_module_encoder(name: str, direction: Direction, /) -> type[_stdlib_json.JSONEncoder]:
    """Return a `JSONEncoder` for the module profile specified by `name` and `direction`."""
    return get_encoder(_json.get_module_serialization_profile_name(name, direction == Direction.CONTROLLER_TO_MODULE))


def get_module_decoder(name: str, direction: Direction, /) -> type[_stdlib_json.JSONDecoder]:
    """Return a `JSONDecoder` for the module profile specified by `name` and `direction`."""
    return get_decoder(_json.get_module_serialization_profile_name(name, direction == Direction.CONTROLLER_TO_MODULE))
