"""Backwards compatibility types, which will be deprecated a future release. Do not use these in new code."""

from __future__ import annotations as _annotations

import typing as _t

from ansible.module_utils._internal import _datatag
from ansible.module_utils.common.text import converters as _converters
from ansible.parsing import vault as _vault

_UNSET = _t.cast(_t.Any, object())


class _AnsibleMapping(dict):
    """Backwards compatibility type."""

    def __new__(cls, value=_UNSET, /, **kwargs):
        if value is _UNSET:
            return dict(**kwargs)

        return _datatag.AnsibleTagHelper.tag_copy(value, dict(value, **kwargs))


class _AnsibleUnicode(str):
    """Backwards compatibility type."""

    def __new__(cls, object=_UNSET, **kwargs):
        if object is _UNSET:
            return str(**kwargs)

        return _datatag.AnsibleTagHelper.tag_copy(object, str(object, **kwargs))


class _AnsibleSequence(list):
    """Backwards compatibility type."""

    def __new__(cls, value=_UNSET, /):
        if value is _UNSET:
            return list()

        return _datatag.AnsibleTagHelper.tag_copy(value, list(value))


class _AnsibleVaultEncryptedUnicode:
    """Backwards compatibility type."""

    def __new__(cls, ciphertext: str | bytes):
        encrypted_string = _vault.EncryptedString(ciphertext=_converters.to_text(_datatag.AnsibleTagHelper.untag(ciphertext)))

        return _datatag.AnsibleTagHelper.tag_copy(ciphertext, encrypted_string)


def __getattr__(name: str) -> _t.Any:
    """Inject import-time deprecation warnings."""
    if (value := globals().get(f'_{name}', None)) and name.startswith('Ansible'):
        # deprecated: description='enable deprecation of everything in this module', core_version='2.23'
        # from ansible.utils.display import Display
        #
        # Display().deprecated(
        #     msg=f"Importing {name!r} is deprecated.",
        #     help_text="Instances of this type cannot be created and will not be encountered.",
        #     version="2.27",
        # )

        return value

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
