from __future__ import annotations

import abc
import collections.abc as c
import enum
import inspect
import itertools
import typing as t

from jinja2 import UndefinedError, StrictUndefined, TemplateRuntimeError
from jinja2.utils import missing

from ...module_utils._internal import _messages
from ansible.constants import config
from ansible.errors import AnsibleUndefinedVariable, AnsibleTypeError
from ansible._internal._errors._handler import ErrorHandler
from ansible.module_utils._internal._datatag import Tripwire, _untaggable_types

from ._access import NotifiableAccessContextBase
from ._jinja_patches import _patch_jinja
from ._utils import TemplateContext
from .._errors import _captured
from ...module_utils.datatag import native_type_name

_patch_jinja()  # apply Jinja2 patches before types are declared that are dependent on the changes


class _SandboxMode(enum.Enum):
    DEFAULT = enum.auto()
    ALLOW_UNSAFE_ATTRIBUTES = enum.auto()


class _TemplateConfig:
    allow_embedded_templates: bool = config.get_config_value("ALLOW_EMBEDDED_TEMPLATES")
    allow_broken_conditionals: bool = config.get_config_value('ALLOW_BROKEN_CONDITIONALS')
    jinja_extensions: list[str] = config.get_config_value('DEFAULT_JINJA2_EXTENSIONS')
    sandbox_mode: _SandboxMode = _SandboxMode.__members__[config.get_config_value('_TEMPLAR_SANDBOX_MODE').upper()]

    unknown_type_encountered_handler = ErrorHandler.from_config('_TEMPLAR_UNKNOWN_TYPE_ENCOUNTERED')
    unknown_type_conversion_handler = ErrorHandler.from_config('_TEMPLAR_UNKNOWN_TYPE_CONVERSION')
    untrusted_template_handler = ErrorHandler.from_config('_TEMPLAR_UNTRUSTED_TEMPLATE_BEHAVIOR')


class MarkerError(UndefinedError):
    """
    An Ansible specific subclass of Jinja's UndefinedError, used to preserve and later restore the original Marker instance that raised the error.
    This error is only raised by Marker and should never escape the templating system.
    """

    def __init__(self, message: str, source: Marker) -> None:
        super().__init__(message)

        self.source = source


class Marker(StrictUndefined, Tripwire):
    """
    Extends Jinja's `StrictUndefined`, allowing any kind of error occurring during recursive templating operations to be captured and deferred.
    Direct or managed access to most `Marker` attributes will raise a `MarkerError`, which usually ends the current innermost templating
    operation and converts the `MarkerError` back to the origin Marker instance (subject to the `MarkerBehavior` in effect at the time).
    """

    __slots__ = ('_marker_template_source',)

    _concrete_subclasses: t.ClassVar[set[type[Marker]]] = set()

    def __init__(
        self,
        hint: t.Optional[str] = None,
        obj: t.Any = missing,
        name: t.Optional[str] = None,
        exc: t.Type[TemplateRuntimeError] = UndefinedError,  # Ansible doesn't set this argument or consume the attribute it is stored under.
        *args,
        _no_template_source=False,
        **kwargs,
    ) -> None:
        if not hint and name and obj is not missing:
            hint = f"object of type {native_type_name(obj)!r} has no attribute {name!r}"

        kwargs.update(
            hint=hint,
            obj=obj,
            name=name,
            exc=exc,
        )

        super().__init__(*args, **kwargs)

        if _no_template_source:
            self._marker_template_source = None
        else:
            self._marker_template_source = TemplateContext.current().template_value

    def _as_exception(self) -> Exception:
        """Return the exception instance to raise in a top-level templating context."""
        return AnsibleUndefinedVariable(self._undefined_message, obj=self._marker_template_source)

    def _as_message(self) -> str:
        """Return the error message to show when this marker must be represented as a string, such as for substitutions or warnings."""
        return self._undefined_message

    def _fail_with_undefined_error(self, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
        """Ansible-specific replacement for Jinja's _fail_with_undefined_error tripwire on dunder methods."""
        self.trip()

    def trip(self) -> t.NoReturn:
        """Raise an internal exception which can be converted back to this instance."""
        raise MarkerError(self._undefined_message, self)

    def __setattr__(self, name: str, value: t.Any) -> None:
        """
        Any attempt to set an unknown attribute on a `Marker` should invoke the trip method to propagate the original context.
        This does not protect against mutation of known attributes, but the implementation is fairly simple.
        """
        try:
            super().__setattr__(name, value)
        except AttributeError:
            pass
        else:
            return

        self.trip()

    def __getattr__(self, name: str) -> t.Any:
        """Raises AttributeError for dunder-looking accesses, self-propagates otherwise."""
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)

        return self

    def __getitem__(self, key):
        """Self-propagates on all item accesses."""
        return self

    @classmethod
    def __init_subclass__(cls, **kwargs) -> None:
        if not inspect.isabstract(cls):
            _untaggable_types.add(cls)
            cls._concrete_subclasses.add(cls)

    @classmethod
    def _init_class(cls):
        _untaggable_types.add(cls)

        # These are the methods StrictUndefined already intercepts.
        jinja_method_names = (
            '__add__',
            '__bool__',
            '__call__',
            '__complex__',
            '__contains__',
            '__div__',
            '__eq__',
            '__float__',
            '__floordiv__',
            '__ge__',
            # '__getitem__',  # using a custom implementation that propagates self instead
            '__gt__',
            '__hash__',
            '__int__',
            '__iter__',
            '__le__',
            '__len__',
            '__lt__',
            '__mod__',
            '__mul__',
            '__ne__',
            '__neg__',
            '__pos__',
            '__pow__',
            '__radd__',
            '__rdiv__',
            '__rfloordiv__',
            '__rmod__',
            '__rmul__',
            '__rpow__',
            '__rsub__',
            '__rtruediv__',
            '__str__',
            '__sub__',
            '__truediv__',
        )

        # These additional methods should be intercepted, even though they are not intercepted by StrictUndefined.
        additional_method_names = (
            '__aiter__',
            '__delattr__',
            '__format__',
            '__repr__',
            '__setitem__',
        )

        for name in jinja_method_names + additional_method_names:
            setattr(cls, name, cls._fail_with_undefined_error)


Marker._init_class()


class TruncationMarker(Marker):
    """
    An `Marker` value was previously encountered and reported.
    A subsequent `Marker` value (this instance) indicates the template may have been truncated as a result.
    It will only be visible if the previous `Marker` was ignored/replaced instead of being tripped, which would raise an exception.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(hint='template potentially truncated')


class UndefinedMarker(Marker):
    """A `Marker` value that represents an undefined value encountered during templating."""

    __slots__ = ()


class ExceptionMarker(Marker, metaclass=abc.ABCMeta):
    """Base `Marker` class that represents exceptions encountered and deferred during templating."""

    __slots__ = ()

    @abc.abstractmethod
    def _as_exception(self) -> Exception:
        pass

    def _as_message(self) -> str:
        return str(self._as_exception())

    def trip(self) -> t.NoReturn:
        """Raise an internal exception which can be converted back to this instance while maintaining the cause for callers that follow them."""
        raise MarkerError(self._undefined_message, self) from self._as_exception()


class CapturedExceptionMarker(ExceptionMarker):
    """A `Marker` value that represents an exception raised during templating."""

    __slots__ = ('_marker_captured_exception',)

    def __init__(self, exception: Exception) -> None:
        super().__init__(hint=f'A captured exception marker was tripped: {exception}')

        self._marker_captured_exception = exception

    def _as_exception(self) -> Exception:
        return self._marker_captured_exception


class UndecryptableVaultError(_captured.AnsibleCapturedError):
    """Template-external error raised by VaultExceptionMarker when an undecryptable variable is accessed."""

    context = 'vault'
    _default_message = "Attempt to use undecryptable variable."


class VaultExceptionMarker(ExceptionMarker):
    """A `Marker` value that represents an error accessing a vaulted value during templating."""

    __slots__ = ('_marker_undecryptable_ciphertext', '_marker_event')

    def __init__(self, ciphertext: str, event: _messages.Event) -> None:
        super().__init__(hint='A vault exception marker was tripped.')

        self._marker_undecryptable_ciphertext = ciphertext
        self._marker_event = event

    def _as_exception(self) -> Exception:
        return UndecryptableVaultError(
            obj=self._marker_undecryptable_ciphertext,
            event=self._marker_event,
        )

    def _disarm(self) -> str:
        return self._marker_undecryptable_ciphertext


def get_first_marker_arg(args: c.Sequence, kwargs: dict[str, t.Any]) -> Marker | None:
    """Utility method to inspect plugin args and return the first `Marker` encountered, otherwise `None`."""
    # CAUTION: This function is exposed in public API as ansible.template.get_first_marker_arg.
    return next(iter_marker_args(args, kwargs), None)


def iter_marker_args(args: c.Sequence, kwargs: dict[str, t.Any]) -> t.Generator[Marker]:
    """Utility method to iterate plugin args and yield any `Marker` encountered."""
    for arg in itertools.chain(args, kwargs.values()):
        if isinstance(arg, Marker):
            yield arg


class JinjaCallContext(NotifiableAccessContextBase):
    """
    An audit context that wraps all Jinja (template/filter/test/lookup/method/function) calls.
    While active, calls `trip()` on managed access of `Marker` objects unless the callee declares an understanding of markers.
    """

    _mask = True

    def __init__(self, accept_lazy_markers: bool) -> None:
        self._type_interest = frozenset() if accept_lazy_markers else frozenset(Marker._concrete_subclasses)

    def _notify(self, o: Marker) -> t.NoReturn:
        o.trip()


def validate_arg_type(name: str, value: t.Any, allowed_type_or_types: type | tuple[type, ...], /) -> None:
    """Validate the type of the given argument while preserving context for Marker values."""
    # DTFIX-FUTURE: find a home for this as a general-purpose utliity method and expose it after some API review
    if isinstance(value, allowed_type_or_types):
        return

    if isinstance(allowed_type_or_types, type):
        arg_type_description = repr(native_type_name(allowed_type_or_types))
    else:
        arg_type_description = ' or '.join(repr(native_type_name(item)) for item in allowed_type_or_types)

    if isinstance(value, Marker):
        try:
            value.trip()
        except Exception as ex:
            raise AnsibleTypeError(f"The {name!r} argument must be of type {arg_type_description}.", obj=value) from ex

    raise AnsibleTypeError(f"The {name!r} argument must be of type {arg_type_description}, not {native_type_name(value)!r}.", obj=value)
