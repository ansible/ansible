"""
Message contract definitions for various target-side types.

These types and the wire format they implement are currently considered provisional and subject to change without notice.
A future release will remove the provisional status.
"""

from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import enum as _enum
import sys as _sys
import typing as _t

from ansible.module_utils._internal import _datatag, _dataclass_validation

if _sys.version_info >= (3, 10):
    # Using slots for reduced memory usage and improved performance.
    _dataclass_kwargs = dict(frozen=True, kw_only=True, slots=True)
else:
    # deprecated: description='always use dataclass slots and keyword-only args' python_version='3.9'
    _dataclass_kwargs = dict(frozen=True)


class PluginType(_datatag.AnsibleSerializableEnum):
    """Enum of Ansible plugin types."""

    ACTION = _enum.auto()
    BECOME = _enum.auto()
    CACHE = _enum.auto()
    CALLBACK = _enum.auto()
    CLICONF = _enum.auto()
    CONNECTION = _enum.auto()
    DOC_FRAGMENTS = _enum.auto()
    FILTER = _enum.auto()
    HTTPAPI = _enum.auto()
    INVENTORY = _enum.auto()
    LOOKUP = _enum.auto()
    MODULE = _enum.auto()
    NETCONF = _enum.auto()
    SHELL = _enum.auto()
    STRATEGY = _enum.auto()
    TERMINAL = _enum.auto()
    TEST = _enum.auto()
    VARS = _enum.auto()


@_dataclasses.dataclass(**_dataclass_kwargs)
class PluginInfo(_datatag.AnsibleSerializableDataclass):
    """Information about a loaded plugin."""

    resolved_name: _t.Optional[str]
    """The resolved canonical plugin name; always fully-qualified for collection plugins."""

    type: _t.Optional[PluginType]
    """The plugin type."""


@_dataclasses.dataclass(**_dataclass_kwargs)
class EventChain(_datatag.AnsibleSerializableDataclass):
    """A chain used to link one event to another."""

    _validation_auto_enabled = False

    def __post_init__(self): ...  # required for deferred dataclass validation

    msg_reason: str
    traceback_reason: str
    event: Event
    follow: bool = True


@_dataclasses.dataclass(**_dataclass_kwargs)
class Event(_datatag.AnsibleSerializableDataclass):
    """Base class for an error/warning/deprecation event with optional chain (from an exception __cause__ chain) and an optional traceback."""

    _validation_auto_enabled = False

    def __post_init__(self): ...  # required for deferred dataclass validation

    msg: str
    formatted_source_context: _t.Optional[str] = None
    formatted_traceback: _t.Optional[str] = None
    help_text: _t.Optional[str] = None
    chain: _t.Optional[EventChain] = None
    events: _t.Optional[_t.Tuple[Event, ...]] = None


_dataclass_validation.inject_post_init_validation(EventChain, EventChain._validation_allow_subclasses)
_dataclass_validation.inject_post_init_validation(Event, Event._validation_allow_subclasses)


@_dataclasses.dataclass(**_dataclass_kwargs)
class SummaryBase(_datatag.AnsibleSerializableDataclass):
    """Base class for an error/warning/deprecation summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""

    event: Event


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
