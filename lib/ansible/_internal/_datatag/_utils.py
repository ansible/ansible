from __future__ import annotations

from ansible.module_utils._internal._datatag import AnsibleTagHelper


def str_problematic_strip(value: str) -> str:
    """
    Return a copy of `value` with leading and trailing whitespace removed.
    Used where `str.strip` is needed, but tags must be preserved *AND* the stripping behavior likely shouldn't exist.
    If the stripping behavior is non-problematic, use `AnsibleTagHelper.tag_copy` around `str.strip` instead.
    """
    if (stripped_value := value.strip()) == value:
        return value

    # FUTURE: consider deprecating some/all usages of this method; they generally imply a code smell or pattern we shouldn't be supporting

    stripped_value = AnsibleTagHelper.tag_copy(value, stripped_value)

    return stripped_value
