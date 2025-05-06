"""
Message contract definitions for various target-side types.

These types and the wire format they implement are currently considered provisional and subject to change without notice.
A future release will remove the provisional status.
"""

from __future__ import annotations as _annotations

import sys as _sys
import dataclasses as _dataclasses

# deprecated: description='typing.Self exists in Python 3.11+' python_version='3.10'
from ..compat import typing as _t

from ansible.module_utils._internal import _datatag, _validation

if _sys.version_info >= (3, 10):
    # Using slots for reduced memory usage and improved performance.
    _dataclass_kwargs = dict(frozen=True, kw_only=True, slots=True)
else:
    # deprecated: description='always use dataclass slots and keyword-only args' python_version='3.9'
    _dataclass_kwargs = dict(frozen=True)


@_dataclasses.dataclass(**_dataclass_kwargs)
class PluginInfo(_datatag.AnsibleSerializableDataclass):
    """Information about a loaded plugin."""

    resolved_name: str
    """The resolved canonical plugin name; always fully-qualified for collection plugins."""
    type: str
    """The plugin type."""

    _COLLECTION_ONLY_TYPE: _t.ClassVar[str] = 'collection'
    """This is not a real plugin type. It's a placeholder for use by a `PluginInfo` instance which references a collection without a plugin."""

    @classmethod
    def _from_collection_name(cls, collection_name: str | None) -> _t.Self | None:
        """Returns an instance with the special `collection` type to refer to a non-plugin or ambiguous caller within a collection."""
        if not collection_name:
            return None

        _validation.validate_collection_name(collection_name)

        return cls(
            resolved_name=collection_name,
            type=cls._COLLECTION_ONLY_TYPE,
        )


@_dataclasses.dataclass(**_dataclass_kwargs)
class Detail(_datatag.AnsibleSerializableDataclass):
    """Message detail with optional source context and help text."""

    msg: str
    formatted_source_context: _t.Optional[str] = None
    help_text: _t.Optional[str] = None


@_dataclasses.dataclass(**_dataclass_kwargs)
class SummaryBase(_datatag.AnsibleSerializableDataclass):
    """Base class for an error/warning/deprecation summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""

    details: _t.Tuple[Detail, ...]
    formatted_traceback: _t.Optional[str] = None

    def _format(self) -> str:
        """Returns a string representation of the details."""
        # DTFIX-RELEASE: eliminate this function and use a common message squashing utility such as get_chained_message on instances of this type
        return ': '.join(detail.msg for detail in self.details)

    def _post_validate(self) -> None:
        if not self.details:
            raise ValueError(f'{type(self).__name__}.details cannot be empty')


@_dataclasses.dataclass(**_dataclass_kwargs)
class ErrorSummary(SummaryBase):
    """Error summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""


@_dataclasses.dataclass(**_dataclass_kwargs)
class WarningSummary(SummaryBase):
    """Warning summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""


@_dataclasses.dataclass(**_dataclass_kwargs)
class DeprecationSummary(WarningSummary):
    """Deprecation summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""

    deprecator: _t.Optional[PluginInfo] = None
    """
    The identifier for the content which is being deprecated.
    """

    date: _t.Optional[str] = None
    """
    The date after which a new release of `deprecator` will remove the feature described by `msg`.
    Ignored if `deprecator` is not provided.
    """

    version: _t.Optional[str] = None
    """
    The version of `deprecator` which will remove the feature described by `msg`.
    Ignored if `deprecator` is not provided.
    Ignored if `date` is provided.
    """

    def _as_simple_dict(self) -> _t.Dict[str, _t.Any]:
        """Returns a dictionary representation of the deprecation object in the format exposed to playbooks."""
        from ansible.module_utils._internal._deprecator import INDETERMINATE_DEPRECATOR  # circular import from messages

        if self.deprecator and self.deprecator != INDETERMINATE_DEPRECATOR:
            collection_name = '.'.join(self.deprecator.resolved_name.split('.')[:2])
        else:
            collection_name = None

        result = self._as_dict()
        result.update(
            msg=self._format(),
            collection_name=collection_name,
        )

        return result
