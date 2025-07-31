from __future__ import annotations

import copy
import dataclasses
import functools
import types
import typing as t

from jinja2.environment import TemplateModule

from ansible.module_utils._internal._datatag import (
    AnsibleTagHelper,
    AnsibleTaggedObject,
    _AnsibleTaggedDict,
    _AnsibleTaggedList,
    _AnsibleTaggedTuple,
    _NO_INSTANCE_STORAGE,
    _try_get_internal_tags_mapping,
)

from ansible.utils.sentinel import Sentinel
from ansible.errors import AnsibleVariableTypeError
from ansible._internal._errors._handler import Skippable
from ansible.vars.hostvars import HostVarsVars, HostVars

from ._access import AnsibleAccessContext
from ._jinja_common import Marker, _TemplateConfig
from ._utils import TemplateContext, PASS_THROUGH_SCALAR_VAR_TYPES, LazyOptions

if t.TYPE_CHECKING:
    from ._engine import TemplateEngine

_KNOWN_TYPES: t.Final[set[type]] = (
    {
        HostVars,  # example: hostvars
        HostVarsVars,  # example: hostvars.localhost | select
        type,  # example: range(20) | list  # triggered on retrieval of `range` type from globals
        range,  # example: range(20) | list  # triggered when returning a `range` instance from a call
        types.FunctionType,  # example: undef() | default("blah")
        types.MethodType,  # example: ansible_facts.get | type_debug
        functools.partial,
        type(''.startswith),  # example: inventory_hostname.upper | type_debug  # using `startswith` to resolve `builtin_function_or_method`
        TemplateModule,  # example: '{% import "importme.j2" as im %}{{ im | type_debug }}'
    }
    | set(PASS_THROUGH_SCALAR_VAR_TYPES)
    | set(Marker._concrete_subclasses)
)
"""
These types are known to the templating system.
In addition to the statically defined types, additional types will be added at runtime.
When enabled in config, this set will be used to determine if an encountered type should trigger a warning or error.
"""


def register_known_types(*args: type) -> None:
    """Register a type with the template engine so it will not trigger warnings or errors when encountered."""
    _KNOWN_TYPES.update(args)


class UnsupportedConstructionMethodError(RuntimeError):
    """Error raised when attempting to construct a lazy container with unsupported arguments."""

    def __init__(self):
        super().__init__("Direct construction of lazy containers is not supported.")


@t.final
@dataclasses.dataclass(frozen=True, slots=True)
class _LazyValue:
    """Wrapper around values to indicate lazy behavior has not yet been applied."""

    value: t.Any


@t.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _LazyValueSource:
    """Intermediate value source for lazy-eligible collection copy operations."""

    source: t.Iterable
    templar: TemplateEngine
    lazy_options: LazyOptions


@t.final
class _NoKeySentinel(Sentinel):
    """Sentinel used to indicate a requested key was not found."""


# There are several operations performed by lazy containers, with some variation between types.
#
# Columns: D=dict, L=list, T=tuple
#   Cells: l=lazy (upon access), n=non-lazy (__init__/__new__)
#
# D  L  T  Feature      Description
# -  -  -  -----------  ---------------------------------------------------------------
# l  l  n  propagation  when container items which are containers become lazy instances
# l  l  n  transform    when transforms are applied to container items
# l  l  n  templating   when templating is performed on container items
# l  l  l  access       when access calls are performed on container items


class _AnsibleLazyTemplateMixin:
    __slots__ = _NO_INSTANCE_STORAGE

    _dispatch_types: t.ClassVar[dict[type, type[_AnsibleLazyTemplateMixin]]] = {}  # populated by __init_subclass__
    _container_types: t.ClassVar[set[type]] = set()  # populated by __init_subclass__

    _native_type: t.ClassVar[type]  # from AnsibleTaggedObject

    _SLOTS: t.Final = (
        '_templar',
        '_lazy_options',
    )

    _templar: TemplateEngine
    _lazy_options: LazyOptions

    def __init_subclass__(cls, **kwargs) -> None:
        tagged_type = cls.__mro__[1]
        native_type = tagged_type.__mro__[1]

        for check_type in (tagged_type, native_type):
            if conflicting_type := cls._dispatch_types.get(check_type):
                raise TypeError(f"Lazy mixin {cls.__name__!r} type {check_type.__name__!r} conflicts with {conflicting_type.__name__!r}.")

        cls._dispatch_types[native_type] = cls
        cls._dispatch_types[tagged_type] = cls
        cls._container_types.add(native_type)
        cls._empty_tags_as_native = False  # never revert to the native type when no tags remain

        register_known_types(cls)

    def __init__(self, contents: t.Iterable | _LazyValueSource) -> None:
        if isinstance(contents, _LazyValueSource):
            self._templar = contents.templar
            self._lazy_options = contents.lazy_options
        elif isinstance(contents, _AnsibleLazyTemplateMixin):
            self._templar = contents._templar
            self._lazy_options = contents._lazy_options
        else:
            raise UnsupportedConstructionMethodError()

    def __reduce_ex__(self, protocol):
        raise NotImplementedError("Pickling of Ansible lazy objects is not permitted.")

    @staticmethod
    def _try_create(item: t.Any, lazy_options: LazyOptions = LazyOptions.DEFAULT) -> t.Any:
        """
        If `item` is a container type which supports lazy access and/or templating, return a lazy wrapped version -- otherwise return it as-is.
        When returning as-is, a warning or error may be generated for unknown types.
        The `lazy_options.skip_templates` argument should be set to `True` when `item` is sourced from a plugin instead of Ansible variable storage.
        This provides backwards compatibility and reduces lazy overhead, as plugins do not normally introduce templates.
        If a plugin needs to introduce templates, the plugin is responsible for invoking the templar and returning the result.
        """
        item_type = type(item)

        # Try to use exact type match first to determine which wrapper (if any) to apply; isinstance checks
        # are extremely expensive, so try to avoid them for our commonly-supported types.
        if (dispatcher := _AnsibleLazyTemplateMixin._dispatch_types.get(item_type)) is not None:
            # Create a generator that yields the elements of `item` wrapped in a `_LazyValue` wrapper.
            # The wrapper is used to signal to the lazy container that the value must be processed before being returned.
            # Values added to the lazy container later through other means will be returned as-is, without any special processing.
            lazy_values = dispatcher._lazy_values(item, lazy_options)
            tags_mapping = _try_get_internal_tags_mapping(item)
            value = t.cast(AnsibleTaggedObject, dispatcher)._instance_factory(lazy_values, tags_mapping)

            return value

        with Skippable, _TemplateConfig.unknown_type_encountered_handler.handle(AnsibleVariableTypeError, skip_on_ignore=True):
            if item_type not in _KNOWN_TYPES:
                raise AnsibleVariableTypeError(
                    message=f"Encountered unknown type {item_type.__name__!r} during template operation.",
                    help_text="Use supported types to avoid unexpected behavior.",
                    obj=TemplateContext.current().template_value,
                )

        return item

    def _is_not_lazy_combine_candidate(self, other: object) -> bool:
        """Returns `True` if `other` cannot be lazily combined with the current instance due to differing templar/options, otherwise returns `False`."""
        return isinstance(other, _AnsibleLazyTemplateMixin) and (self._templar is not other._templar or self._lazy_options != other._lazy_options)

    def _non_lazy_copy(self) -> t.Collection:
        """
        Return a non-lazy copy of this collection.
        Any remaining lazy wrapped values will be unwrapped without further processing.
        Tags on this instance will be preserved on the returned copy.
        """
        raise NotImplementedError()  # pragma: nocover

    @staticmethod
    def _lazy_values(values: t.Any, lazy_options: LazyOptions) -> _LazyValueSource:
        """
        Return an iterable that wraps each of the given elements in a lazy wrapper.
        Only elements wrapped this way will receive lazy processing when retrieved from the collection.
        """
        # DTFIX-FUTURE: check relative performance of method-local vs stored generator expressions on implementations of this method
        raise NotImplementedError()  # pragma: nocover

    def _proxy_or_render_lazy_value(self, key: t.Any, value: t.Any) -> t.Any:
        """
        Ensure that the value is lazy-proxied or rendered, and if a key is provided, replace the original value with the result.
        """
        if type(value) is not _LazyValue:  # pylint: disable=unidiomatic-typecheck
            if self._lazy_options.access:
                AnsibleAccessContext.current().access(value)

            return value

        original_value = value.value

        if self._lazy_options.access:
            AnsibleAccessContext.current().access(original_value)

        new_value = self._templar.template(original_value, lazy_options=self._lazy_options)

        if new_value is not original_value and self._lazy_options.access:
            AnsibleAccessContext.current().access(new_value)

        if key is not _NoKeySentinel:
            self._native_type.__setitem__(self, key, new_value)  # type: ignore  # pylint: disable=unnecessary-dunder-call

        return new_value


@t.final  # consumers of lazy collections rely heavily on the concrete types being final
class _AnsibleLazyTemplateDict(_AnsibleTaggedDict, _AnsibleLazyTemplateMixin):
    __slots__ = _AnsibleLazyTemplateMixin._SLOTS

    def __init__(self, contents: t.Iterable | _LazyValueSource, /, **kwargs) -> None:
        if isinstance(contents, _AnsibleLazyTemplateDict):
            super().__init__(dict.items(contents), **kwargs)
        elif isinstance(contents, _LazyValueSource):
            super().__init__(contents.source, **kwargs)
        else:
            raise UnsupportedConstructionMethodError()

        _AnsibleLazyTemplateMixin.__init__(self, contents)

    def get(self, key: t.Any, default: t.Any = None) -> t.Any:
        if (value := super().get(key, _NoKeySentinel)) is _NoKeySentinel:
            return default

        return self._proxy_or_render_lazy_value(key, value)

    def __getitem__(self, key: t.Any, /) -> t.Any:
        return self._proxy_or_render_lazy_value(key, super().__getitem__(key))

    def __str__(self):
        return str(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    def __repr__(self):
        return repr(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    def __iter__(self):
        # We're using the base implementation, but must override `__iter__` to skip `dict` fast-path copy, which would bypass lazy behavior.
        # See: https://github.com/python/cpython/blob/ffcc450a9b8b6927549b501eff7ac14abc238448/Objects/dictobject.c#L3861-L3864
        return super().__iter__()

    def setdefault(self, key, default=None, /) -> t.Any:
        if (value := self.get(key, _NoKeySentinel)) is not _NoKeySentinel:
            return value

        super().__setitem__(key, default)

        return default

    def items(self):
        for key, value in super().items():
            yield key, self._proxy_or_render_lazy_value(key, value)

    def values(self):
        for _key, value in self.items():
            yield value

    def pop(self, key, default=_NoKeySentinel, /) -> t.Any:
        if (value := super().get(key, _NoKeySentinel)) is _NoKeySentinel:
            if default is _NoKeySentinel:
                raise KeyError(key)

            return default

        value = self._proxy_or_render_lazy_value(_NoKeySentinel, value)

        del self[key]

        return value

    def popitem(self) -> t.Any:
        try:
            key = next(reversed(self))
        except StopIteration:
            raise KeyError("popitem(): dictionary is empty")

        value = self._proxy_or_render_lazy_value(_NoKeySentinel, self[key])

        del self[key]

        return key, value

    def _native_copy(self) -> dict:
        return dict(self.items())

    @staticmethod
    def _item_source(value: dict) -> dict | _LazyValueSource:
        if isinstance(value, _AnsibleLazyTemplateDict):
            return _LazyValueSource(source=dict.items(value), templar=value._templar, lazy_options=value._lazy_options)

        return value

    def _yield_non_lazy_dict_items(self) -> t.Iterator[tuple[str, t.Any]]:
        """
        Delegate to the base collection items iterator to yield the raw contents.
        As of Python 3.13, generator functions are significantly faster than inline generator expressions.
        """
        for k, v in dict.items(self):
            yield k, v.value if type(v) is _LazyValue else v  # pylint: disable=unidiomatic-typecheck

    def _non_lazy_copy(self) -> dict:
        return AnsibleTagHelper.tag_copy(self, self._yield_non_lazy_dict_items(), value_type=dict)

    @staticmethod
    def _lazy_values(values: dict, lazy_options: LazyOptions) -> _LazyValueSource:
        return _LazyValueSource(source=((k, _LazyValue(v)) for k, v in values.items()), templar=TemplateContext.current().templar, lazy_options=lazy_options)

    @staticmethod
    def _proxy_or_render_other(other: t.Any | None) -> None:
        """Call `_proxy_or_render_lazy_values` if `other` is a lazy dict. Used internally by comparison methods."""
        if type(other) is _AnsibleLazyTemplateDict:  # pylint: disable=unidiomatic-typecheck
            other._proxy_or_render_lazy_values()

    def _proxy_or_render_lazy_values(self) -> None:
        """Ensure all `_LazyValue` wrapped values have been processed."""
        for _unused in self.values():
            pass

    def __eq__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__eq__(other)

    def __ne__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__ne__(other)

    def __or__(self, other):
        # DTFIX-FUTURE: support preservation of laziness when possible like we do for list
        # Both sides end up going through _proxy_or_render_lazy_value, so there's no Templar preservation needed.
        # In the future this could be made more lazy when both Templar instances are the same, or if per-value Templar tracking was used.
        return super().__or__(other)

    def __ror__(self, other):
        # DTFIX-FUTURE: support preservation of laziness when possible like we do for list
        # Both sides end up going through _proxy_or_render_lazy_value, so there's no Templar preservation needed.
        # In the future this could be made more lazy when both Templar instances are the same, or if per-value Templar tracking was used.
        return super().__ror__(other)

    def __deepcopy__(self, memo):
        return _AnsibleLazyTemplateDict(
            _LazyValueSource(
                source=((copy.deepcopy(k), copy.deepcopy(v)) for k, v in super().items()),
                templar=copy.deepcopy(self._templar),
                lazy_options=copy.deepcopy(self._lazy_options),
            )
        )


@t.final  # consumers of lazy collections rely heavily on the concrete types being final
class _AnsibleLazyTemplateList(_AnsibleTaggedList, _AnsibleLazyTemplateMixin):
    __slots__ = _AnsibleLazyTemplateMixin._SLOTS

    def __init__(self, contents: t.Iterable | _LazyValueSource, /) -> None:
        if isinstance(contents, _AnsibleLazyTemplateList):
            super().__init__(list.__iter__(contents))
        elif isinstance(contents, _LazyValueSource):
            super().__init__(contents.source)
        else:
            raise UnsupportedConstructionMethodError()

        _AnsibleLazyTemplateMixin.__init__(self, contents)

    def __getitem__(self, key: t.SupportsIndex | slice, /) -> t.Any:
        if type(key) is slice:  # pylint: disable=unidiomatic-typecheck
            return _AnsibleLazyTemplateList(_LazyValueSource(source=super().__getitem__(key), templar=self._templar, lazy_options=self._lazy_options))

        return self._proxy_or_render_lazy_value(key, super().__getitem__(key))

    def __iter__(self):
        for key, value in enumerate(super().__iter__()):
            yield self._proxy_or_render_lazy_value(key, value)

    def pop(self, idx: t.SupportsIndex = -1, /) -> t.Any:
        if not self:
            raise IndexError('pop from empty list')

        try:
            value = self[idx]
        except IndexError:
            raise IndexError('pop index out of range')

        value = self._proxy_or_render_lazy_value(_NoKeySentinel, value)

        del self[idx]

        return value

    def __str__(self):
        return str(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    def __repr__(self):
        return repr(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    @staticmethod
    def _item_source(value: list) -> list | _LazyValueSource:
        if isinstance(value, _AnsibleLazyTemplateList):
            return _LazyValueSource(source=list.__iter__(value), templar=value._templar, lazy_options=value._lazy_options)

        return value

    def _yield_non_lazy_list_items(self):
        """
        Delegate to the base collection iterator to yield the raw contents.
        As of Python 3.13, generator functions are significantly faster than inline generator expressions.
        """
        for v in list.__iter__(self):
            yield v.value if type(v) is _LazyValue else v  # pylint: disable=unidiomatic-typecheck

    def _non_lazy_copy(self) -> list:
        return AnsibleTagHelper.tag_copy(self, self._yield_non_lazy_list_items(), value_type=list)

    @staticmethod
    def _lazy_values(values: list, lazy_options: LazyOptions) -> _LazyValueSource:
        return _LazyValueSource(source=(_LazyValue(v) for v in values), templar=TemplateContext.current().templar, lazy_options=lazy_options)

    @staticmethod
    def _proxy_or_render_other(other: t.Any | None) -> None:
        """Call `_proxy_or_render_lazy_values` if `other` is a lazy list. Used internally by comparison methods."""
        if type(other) is _AnsibleLazyTemplateList:  # pylint: disable=unidiomatic-typecheck
            other._proxy_or_render_lazy_values()

    def _proxy_or_render_lazy_values(self) -> None:
        """Ensure all `_LazyValue` wrapped values have been processed."""
        for _unused in self:
            pass

    def __eq__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__eq__(other)

    def __ne__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__ne__(other)

    def __gt__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__gt__(other)

    def __ge__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__ge__(other)

    def __lt__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__lt__(other)

    def __le__(self, other):
        self._proxy_or_render_lazy_values()
        self._proxy_or_render_other(other)
        return super().__le__(other)

    def __contains__(self, item):
        self._proxy_or_render_lazy_values()
        return super().__contains__(item)

    def __reversed__(self):
        for idx in range(self.__len__() - 1, -1, -1):
            yield self[idx]

    def __add__(self, other):
        if self._is_not_lazy_combine_candidate(other):
            # When other is lazy with a different templar/options, it cannot be lazily combined with self and a plain list must be returned.
            # If other is a list, de-lazify both, otherwise just let the operation fail.

            if isinstance(other, _AnsibleLazyTemplateList):
                self._proxy_or_render_lazy_values()
                other._proxy_or_render_lazy_values()

            return super().__add__(other)

        # For all other cases, the new list inherits our templar and all values stay lazy.
        # We use list.__add__ to avoid implementing all its error behavior.
        return _AnsibleLazyTemplateList(_LazyValueSource(source=super().__add__(other), templar=self._templar, lazy_options=self._lazy_options))

    def __radd__(self, other):
        if not (other_add := getattr(other, '__add__', None)):
            raise TypeError(f'unsupported operand type(s) for +: {type(other).__name__!r} and {type(self).__name__!r}') from None

        return _AnsibleLazyTemplateList(_LazyValueSource(source=other_add(self), templar=self._templar, lazy_options=self._lazy_options))

    def __mul__(self, other):
        return _AnsibleLazyTemplateList(_LazyValueSource(source=super().__mul__(other), templar=self._templar, lazy_options=self._lazy_options))

    def __rmul__(self, other):
        return _AnsibleLazyTemplateList(_LazyValueSource(source=super().__rmul__(other), templar=self._templar, lazy_options=self._lazy_options))

    def index(self, *args, **kwargs) -> int:
        self._proxy_or_render_lazy_values()
        return super().index(*args, **kwargs)

    def remove(self, *args, **kwargs) -> None:
        self._proxy_or_render_lazy_values()
        super().remove(*args, **kwargs)

    def sort(self, *args, **kwargs) -> None:
        self._proxy_or_render_lazy_values()
        super().sort(*args, **kwargs)

    def __deepcopy__(self, memo):
        return _AnsibleLazyTemplateList(
            _LazyValueSource(
                source=(copy.deepcopy(v) for v in super().__iter__()),
                templar=copy.deepcopy(self._templar),
                lazy_options=copy.deepcopy(self._lazy_options),
            )
        )


@t.final  # consumers of lazy collections rely heavily on the concrete types being final
class _AnsibleLazyAccessTuple(_AnsibleTaggedTuple, _AnsibleLazyTemplateMixin):
    """
    A tagged tuple subclass that provides only managed access for existing lazy values.

    Since tuples are immutable, they cannot support lazy templating (which would change the tuple's value as templates were resolved).
    When this type is created, each value in the source tuple is lazified:

    * template strings are templated immediately (possibly resulting in lazy containers)
    * non-tuple containers are lazy-wrapped
    * tuples are immediately recursively lazy-wrapped
    * transformations are applied immediately

    The resulting object provides only managed access to its values (e.g., deprecation warnings, tripwires), and propagates to new lazy containers
    created as a results of managed access.
    """

    # DTFIX5: ensure we have tests that explicitly verify this behavior

    # nonempty __slots__ not supported for subtype of 'tuple'

    def __new__(cls, contents: t.Iterable | _LazyValueSource, /) -> t.Self:
        if isinstance(contents, _AnsibleLazyAccessTuple):
            return super().__new__(cls, tuple.__iter__(contents))

        if isinstance(contents, _LazyValueSource):
            return super().__new__(cls, contents.source)

        raise UnsupportedConstructionMethodError()

    def __init__(self, contents: t.Iterable | _LazyValueSource, /) -> None:
        _AnsibleLazyTemplateMixin.__init__(self, contents)

    def __getitem__(self, key: t.SupportsIndex | slice, /) -> t.Any:
        if type(key) is slice:  # pylint: disable=unidiomatic-typecheck
            return _AnsibleLazyAccessTuple(_LazyValueSource(source=super().__getitem__(key), templar=self._templar, lazy_options=self._lazy_options))

        value = super().__getitem__(key)

        if self._lazy_options.access:
            AnsibleAccessContext.current().access(value)

        return value

    @staticmethod
    def _item_source(value: tuple) -> tuple | _LazyValueSource:
        if isinstance(value, _AnsibleLazyAccessTuple):
            return _LazyValueSource(source=tuple.__iter__(value), templar=value._templar, lazy_options=value._lazy_options)

        return value

    @staticmethod
    def _lazy_values(values: t.Any, lazy_options: LazyOptions) -> _LazyValueSource:
        templar = TemplateContext.current().templar

        return _LazyValueSource(source=(templar.template(value, lazy_options=lazy_options) for value in values), templar=templar, lazy_options=lazy_options)

    def _non_lazy_copy(self) -> tuple:
        return AnsibleTagHelper.tag_copy(self, self, value_type=tuple)

    def __deepcopy__(self, memo):
        return _AnsibleLazyAccessTuple(
            _LazyValueSource(
                source=(copy.deepcopy(v) for v in super().__iter__()),
                templar=copy.deepcopy(self._templar),
                lazy_options=copy.deepcopy(self._lazy_options),
            )
        )


def lazify_container(value: t.Any) -> t.Any:
    """
    If the given value is a supported container type, return its lazy version, otherwise return the value as-is.
    This is used to ensure that managed access and templating occur on args and kwargs to a callable, even if they were sourced from Jinja constants.

    Since both variable access and plugin output are already lazified, this mostly affects Jinja constant containers.
    However, plugins that directly invoke other plugins (e.g., `Environment.call_filter`) are another potential source of non-lazy containers.
    In these cases, templating will occur for trusted templates automatically upon access.

    Sets, tuples, and dictionary keys cannot be lazy, since their correct operation requires hashability and equality.
    These properties are mutually exclusive with the following lazy features:

    - managed access on encrypted strings - may raise errors on both operations when decryption fails
    - managed access on markers - must raise errors on both operations
    - templating - mutates values

    That leaves non-raising managed access as the only remaining feature, which is insufficient to warrant lazy support.
    """
    return _AnsibleLazyTemplateMixin._try_create(value)


def lazify_container_args(item: tuple) -> tuple:
    """Return the given args with values converted to lazy containers as needed."""
    return tuple(lazify_container(value) for value in item)


def lazify_container_kwargs(item: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return the given kwargs with values converted to lazy containers as needed."""
    return {key: lazify_container(value) for key, value in item.items()}
