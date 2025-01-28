from __future__ import annotations as _annotations

import enum as _enum
import types as _types

from ansible.module_utils.common import json as _json
from ansible.module_utils._internal import _serialization


class Direction(_enum.Enum):
    MODULE_TO_CONTROLLER = _enum.auto()
    CONTROLLER_TO_MODULE = _enum.auto()


def get_encoder(profile: str | _types.ModuleType, /) -> type[_json.AnsibleProfileJSONEncoder]:
    return _serialization.get_encoder_decoder(profile, _json.AnsibleProfileJSONEncoder)


def get_decoder(profile: str | _types.ModuleType, /) -> type[_json.AnsibleProfileJSONDecoder]:
    return _serialization.get_encoder_decoder(profile, _json.AnsibleProfileJSONDecoder)


def get_module_encoder(name: str, direction: Direction, /) -> type[_json.AnsibleProfileJSONEncoder]:
    return get_encoder(_serialization.get_module_serialization_profile_name(name, direction == Direction.CONTROLLER_TO_MODULE))


def get_module_decoder(name: str, direction: Direction, /) -> type[_json.AnsibleProfileJSONDecoder]:
    return get_decoder(_serialization.get_module_serialization_profile_name(name, direction == Direction.CONTROLLER_TO_MODULE))
