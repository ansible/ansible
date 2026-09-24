from __future__ import annotations

import collections.abc as _c
import typing as _t

from ansible.module_utils._internal._datatag import AnsibleTaggedObject, AnsibleTagHelper
from ansible.module_utils._internal._secrets import _MINIMUM_SECRET_LENGTH, AnsibleSecretMaskError, SecretMasker, _secret_masker

_K = _t.TypeVar("_K")
_V = _t.TypeVar("_V")


@_t.overload
def mask_object(
    value: dict[_K, _V],
    /,
    *,
    mask_placeholder: str = ...,
    lines_keys: dict[str, str] | None = ...,
) -> dict[_K | str, _V | str]: ...  # pragma: nocover


@_t.overload
def mask_object(
    value: list[_V],
    /,
    *,
    mask_placeholder: str = ...,
    lines_keys: dict[str, str] | None = ...,
) -> list[_V | str]: ...  # pragma: nocover


# FUTURE: Look at making this a public API, for now kept internal.
def mask_object(
    value: dict | list,
    /,
    *,
    mask_placeholder: str = "$REDACTED$",
    lines_keys: dict[str, str] | None = None,
) -> dict | list:
    """
    Recursively mask registered secrets in the dict or list ``value``.

    The ``lines_keys`` option maps the key of a text value to the key holding that text split into lines, such as
    {'stdout': 'stdout_lines'}. A secret spanning multiple lines won't match to the registered secret so this mapping
    allows the masker to rebuild the splitlines() from the newly masked value. This mapping happens under every dict in
    the object graph recursively.
    """
    masker = _secret_masker

    with masker._lock:
        if not masker._forms:
            return value

        try:
            return _Walker(masker, mask_placeholder, lines_keys or {}).mask(value)
        except AnsibleSecretMaskError:
            raise
        except Exception:
            # We deliberately do not include the value or original exception
            # to avoid leaking secrets through the exception.
            raise AnsibleSecretMaskError("secret masking failed") from None


class _Walker:
    """Masks every string in an object graph with a masker whose lock is already held."""

    def __init__(self, masker: SecretMasker, placeholder: str, lines_keys: dict[str, str]) -> None:
        self._masker = masker
        self._placeholder = placeholder
        self._lines_items = tuple(lines_keys.items())
        self._tracked_keys = frozenset(lines_keys) | frozenset(lines_keys.values())

    def mask(self, value: _t.Any) -> _t.Any:
        masked = self._mask(value)

        # a replaced value (masked string, number turned string, rebuilt or converted container) keeps the tags of the original
        if masked is not value and isinstance(value, AnsibleTaggedObject):
            masked = AnsibleTagHelper.tag_copy(value, masked)

        return masked

    def _mask(self, value: _t.Any) -> _t.Any:
        # We short circuit for types we know we cannot or should not mask.
        if value is None or isinstance(value, (bool, bytearray, bytes)):
            return value

        if isinstance(value, str):
            return self._masker.mask_string(value, mask_placeholder=self._placeholder, acquire_lock=False)

        if isinstance(value, (int, float)):
            text = str(value)

            if len(text) < _MINIMUM_SECRET_LENGTH:
                return value

            masked = self._masker.mask_string(text, mask_placeholder=self._placeholder, acquire_lock=False)

            return value if masked is text else masked

        if isinstance(value, _c.Mapping):
            return self._mask_mapping(value)

        if isinstance(value, _c.Sequence):
            return self._mask_sequence(value)

        if isinstance(value, _c.Set):
            return {self.mask(item) for item in value}

        return value

    def _mask_mapping(self, value: _c.Mapping) -> _c.Mapping:
        out = {}
        changed = False

        # Maps the lines keys to their corresponding source text keys so we can
        # re-mask the lines values based on the masked text entries.
        lines_mapping = self._get_derived_lines_keys(value)

        # As the keys may be masked themselves, this tracks the mapping from
        # the original keys to the their new name.
        tracked = {}

        for key, item in value.items():
            new_key = self.mask(key)

            # If the key is part of the derived lines mapping, we pretend it is
            # not masked as it will be re-masked if the source text changed.
            new_item = item if key in lines_mapping else self.mask(item)

            if new_key is not key or new_item is not item:
                changed = True

            if new_key in out:
                # If there is a collision with the newly masked key, we append
                # a numeric suffix until it is unique.
                suffix = 2

                while (candidate := f"{new_key} ({suffix})") in out:
                    suffix += 1

                new_key = candidate

            out[new_key] = new_item

            # Need to keep track of the original key names when redoing the lines values later.
            if key in self._tracked_keys:
                tracked[key] = new_key

        for lines_key, text_key in lines_mapping.items():
            masked_text = out[tracked[text_key]]

            # If the text did not change then we don't need to update the lines value.
            if masked_text is not value[text_key]:
                out[tracked[lines_key]] = AnsibleTagHelper.tag_copy(value[lines_key], masked_text.splitlines())

        return out if changed else value

    def _get_derived_lines_keys(self, value: _c.Mapping) -> dict[str, str]:
        derived: dict[str, str] = {}

        for text_key, lines_key in self._lines_items:
            text = value.get(text_key)

            # Only consider lines values that are actually derived from their corresponding text entry.
            if isinstance(text, str) and value.get(lines_key) == text.splitlines():
                derived[lines_key] = text_key

        return derived

    def _mask_sequence(self, value: _c.Sequence) -> _c.Sequence:
        out: list = []
        changed = False

        for item in value:
            new_item = self.mask(item)

            if new_item is not item:
                changed = True

            out.append(new_item)

        return out if changed else value
