from __future__ import annotations

import pytest
import typing as t

from ansible.module_utils._internal._patches import CallablePatch


class BogusPatch(CallablePatch):
    """Coverage-oriented simulated patch where the patch is required but the original implementation to be patched does not exist."""

    target_container: t.ClassVar = dict
    target_attribute = '_bogus_dict_attr'

    @classmethod
    def is_patch_needed(cls) -> bool:
        return True

    def __call__(self, annotation, cls, a_module, a_type, is_type_predicate) -> bool:
        raise NotImplementedError("should not be called")  # pragma: nocover


def test_bogus_patch():
    with pytest.raises(RuntimeError, match="implementation to be patched .* is not present"):
        BogusPatch.patch()
