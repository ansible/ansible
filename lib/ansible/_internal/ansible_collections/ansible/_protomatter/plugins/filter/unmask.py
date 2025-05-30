from __future__ import annotations

import copy
import dataclasses
import typing as t

from ansible._internal._templating._jinja_common import validate_arg_type
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateMixin
from ansible._internal._templating._transform import _type_transform_mapping
from ansible.errors import AnsibleError


def unmask(value: object, type_names: str | list[str]) -> object:
    """
    Internal filter to suppress automatic type transformation in Jinja (e.g., WarningSummary, DeprecationSummary, ErrorSummary).
    Lazy collection caching is in play - the first attempt to access a value in a given lazy container must be with unmasking in place, or the transformed value
    will already be cached.
    """
    validate_arg_type("type_names", type_names, (str, list))

    if isinstance(type_names, str):
        check_type_names = [type_names]
    else:
        check_type_names = type_names

    valid_type_names = {key.__name__ for key in _type_transform_mapping}
    invalid_type_names = [type_name for type_name in check_type_names if type_name not in valid_type_names]

    if invalid_type_names:
        raise AnsibleError(f'Unknown type name(s): {", ".join(invalid_type_names)}', obj=type_names)

    result: object

    if isinstance(value, _AnsibleLazyTemplateMixin):
        result = copy.copy(value)
        result._lazy_options = dataclasses.replace(
            result._lazy_options,
            unmask_type_names=result._lazy_options.unmask_type_names | frozenset(check_type_names),
        )
    else:
        result = value

    return result


class FilterModule(object):
    @staticmethod
    def filters() -> dict[str, t.Callable]:
        return dict(unmask=unmask)
