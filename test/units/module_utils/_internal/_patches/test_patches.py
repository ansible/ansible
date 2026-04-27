"""Test the patching infrastructure."""

from __future__ import annotations

import importlib
import pkgutil
import sys
import typing as t

import pytest

from ansible.module_utils._internal import _patches
from ansible.module_utils._internal._patches import _socket_patch
from ansible.module_utils.common._utils import get_all_subclasses

module_to_patch = sys.modules[__name__]


def import_all_patches() -> None:
    """Import all patch modules so they're discoverable via `concrete_patch_types`."""
    for module_info in pkgutil.iter_modules(_patches.__path__, f'{_patches.__name__}.'):
        importlib.import_module(module_info.name)


def get_patch_types() -> list[type[_patches.CallablePatch]]:
    """Return a sorted list of all imported patches."""
    return sorted(get_all_subclasses(_patches.CallablePatch), key=lambda item: item.__name__)


def get_patch_required_test_cases() -> list:
    """
    Return a list of test cases for checking if patches have been applied.
    If a patch is not needed for a given Python version it will be marked as xfail.
    """
    import_all_patches()

    xfail_patch_when: dict[type[_patches.CallablePatch], bool] = {
        # Example:
        # _patches._some_patch_module.SomePatchClass: sys.version_info >= (3, 13),
        _socket_patch.GetAddrInfoPatch: sys.version_info >= (3, 14),
    }

    patches = sorted(get_all_subclasses(_patches.CallablePatch), key=lambda item: item.__name__)
    patches = [pytest.param(patch, marks=pytest.mark.xfail) if xfail_patch_when.get(patch) else patch for patch in patches]

    return patches


@pytest.mark.parametrize("patch", get_patch_required_test_cases())
def test_patch_required(patch: _patches.CallablePatch) -> None:
    """
    Verify the patch is actually required on the currently running Python version.
    It's possible a future Python version may no longer require the patch.
    If this test fails, verify the patch is not required before ignoring the failure for the affected Python versions.
    """
    assert patch.is_patched()


@pytest.mark.parametrize("patch", get_patch_types())
def test_reload_patch(patch: type[_patches.CallablePatch]) -> None:
    """Make sure that reloading the patch doesn't end up double patching."""
    original_patch = patch
    original_patch_module = sys.modules[original_patch.__module__]
    original_callable = original_patch.get_current_implementation()

    current_patch_module = importlib.reload(original_patch_module)

    current_patch = getattr(current_patch_module, original_patch.__name__)
    current_patch.patch()
    current_callable = current_patch.get_current_implementation()

    assert current_patch is not original_patch
    assert current_patch_module is original_patch_module
    assert current_callable is original_callable


@pytest.mark.parametrize("patch", get_patch_types())
def test_delete_and_import_patch(patch: type[_patches.CallablePatch]) -> None:
    """Make sure that deleting and importing the patch doesn't end up double patching."""
    original_patch = patch
    original_patch_module = sys.modules[original_patch.__module__]
    original_callable = original_patch.get_current_implementation()

    del sys.modules[original_patch_module.__name__]

    current_patch_module = importlib.import_module(original_patch_module.__name__)

    current_patch = getattr(current_patch_module, original_patch.__name__)
    current_patch.patch()
    current_callable = current_patch.get_current_implementation()

    assert current_patch is not original_patch
    assert current_patch_module is not original_patch_module
    assert current_callable is original_callable


def func_for_ineffective_patch() -> bool:
    return False


def test_ineffective_patch() -> None:
    """Verify an ineffective patch results in an error being raised."""
    class IneffectivePatch(_patches.CallablePatch):
        target_container: t.ClassVar = module_to_patch
        target_attribute = 'func_for_ineffective_patch'

        @classmethod
        def is_patch_needed(cls) -> bool:
            return True

        def __call__(self) -> bool:
            return True

    original_function = module_to_patch.func_for_ineffective_patch

    with pytest.raises(RuntimeError, match="Validation of '.*' failed after patching."):
        IneffectivePatch.patch()

    assert module_to_patch.func_for_ineffective_patch is original_function


def func_for_patching_is_idempotent() -> bool:
    return False


def test_patching_is_idempotent() -> None:
    """Verify that patching is idempotent."""
    class PatchingIsIdempotentPatch(_patches.CallablePatch):
        target_container: t.ClassVar = module_to_patch
        target_attribute = 'func_for_patching_is_idempotent'

        @classmethod
        def is_patch_needed(cls) -> bool:
            return module_to_patch.func_for_patching_is_idempotent() is False

        def __call__(self) -> bool:
            return True

    original_function = module_to_patch.func_for_patching_is_idempotent

    PatchingIsIdempotentPatch.patch()

    first_patched_function = module_to_patch.func_for_patching_is_idempotent

    PatchingIsIdempotentPatch.patch()

    second_patched_function = module_to_patch.func_for_patching_is_idempotent

    assert first_patched_function is not original_function
    assert first_patched_function is second_patched_function
