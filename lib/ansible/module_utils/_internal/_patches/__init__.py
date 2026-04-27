"""Infrastructure for patching callables with alternative implementations as needed based on patch-specific test criteria."""

from __future__ import annotations

import abc
import typing as t


@t.runtime_checkable
class PatchedTarget(t.Protocol):
    """Runtime-checkable protocol that allows identification of a patched function via `isinstance`."""

    unpatched_implementation: t.Callable


class CallablePatch(abc.ABC):
    """Base class for patches that provides abstractions for validation of broken behavior, installation of patches, and validation of fixed behavior."""

    target_container: t.ClassVar
    """The module object containing the function to be patched."""

    target_attribute: t.ClassVar[str]
    """The attribute name on the target module to patch."""

    unpatched_implementation: t.ClassVar[t.Callable]
    """The unpatched implementation. Available only after the patch has been applied."""

    @classmethod
    @abc.abstractmethod
    def is_patch_needed(cls) -> bool:
        """Returns True if the patch is currently needed. Returns False if the original target does not need the patch or the patch has already been applied."""

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> t.Any:
        """Invoke the patched or original implementation, depending on whether the patch has been applied or not."""

    @classmethod
    def is_patched(cls) -> bool:
        """Returns True if the patch has been applied, otherwise returns False."""
        return isinstance(cls.get_current_implementation(), PatchedTarget)  # using a protocol lets us be more resilient to module unload weirdness

    @classmethod
    def get_current_implementation(cls) -> t.Any:
        """Get the current (possibly patched) implementation from the patch target container."""
        return getattr(cls.target_container, cls.target_attribute)

    @classmethod
    def patch(cls) -> None:
        """Idempotently apply this patch (if needed)."""
        if cls.is_patched():
            return

        cls.unpatched_implementation = cls.get_current_implementation()

        if not cls.is_patch_needed():
            return

        # __call__ requires an instance (otherwise it'll be __new__)
        setattr(cls.target_container, cls.target_attribute, cls())

        if not cls.is_patch_needed():
            return

        setattr(cls.target_container, cls.target_attribute, cls.unpatched_implementation)

        raise RuntimeError(f"Validation of '{cls.target_container.__name__}.{cls.target_attribute}' failed after patching.")
