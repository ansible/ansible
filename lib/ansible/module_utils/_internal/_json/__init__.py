from __future__ import annotations

import importlib
import importlib.util
import types

import typing as t

from ansible.module_utils._internal._json._profiles import AnsibleProfileJSONEncoder, AnsibleProfileJSONDecoder, _JSONSerializationProfile
from ansible.module_utils import _internal

_T = t.TypeVar('_T', AnsibleProfileJSONEncoder, AnsibleProfileJSONDecoder)


def get_encoder_decoder(profile: str | types.ModuleType, return_type: type[_T]) -> type[_T]:
    class_name = 'Encoder' if return_type is AnsibleProfileJSONEncoder else 'Decoder'

    return getattr(get_serialization_module(profile), class_name)


def get_module_serialization_profile_name(name: str, controller_to_module: bool) -> str:
    if controller_to_module:
        name = f'module_{name}_c2m'
    else:
        name = f'module_{name}_m2c'

    return name


def get_module_serialization_profile_module_name(name: str, controller_to_module: bool) -> str:
    return get_serialization_module_name(get_module_serialization_profile_name(name, controller_to_module))


def get_serialization_profile(name: str | types.ModuleType) -> _JSONSerializationProfile:
    return getattr(get_serialization_module(name), '_Profile')


def get_serialization_module(name: str | types.ModuleType) -> types.ModuleType:
    return importlib.import_module(get_serialization_module_name(name))


def get_serialization_module_name(name: str | types.ModuleType) -> str:
    if isinstance(name, str):
        if '.' in name:
            return name  # name is already fully qualified

        target_name = f'{__name__}._profiles._{name}'
    elif isinstance(name, types.ModuleType):
        return name.__name__
    else:
        raise TypeError(f'Name is {type(name)} instead of {str} or {types.ModuleType}.')

    if importlib.util.find_spec(target_name):
        return target_name

    # the value of is_controller can change after import; always pick it up from the module
    if _internal.is_controller:
        controller_name = f'ansible._internal._json._profiles._{name}'

        if importlib.util.find_spec(controller_name):
            return controller_name

    raise ValueError(f'Unknown profile name {name!r}.')
