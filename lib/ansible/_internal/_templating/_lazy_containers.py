from __future__ import annotations

import dataclasses
import functools
import types
import typing as t

from collections import abc as c

from jinja2.environment import TemplateModule

from ansible.module_utils.datatag import (
    AnsibleTaggedObject,
    _AnsibleTaggedDict,
    _AnsibleTaggedList,
    _NO_INSTANCE_STORAGE,
    _try_get_internal_tags_mapping,
    AnsibleTagHelper,
)

from ansible.utils.display import Display
from ansible.utils.sentinel import Sentinel
from ansible.errors import AnsibleVariableTypeError
from ansible.errors.handler import Skippable
from ansible.vars.hostvars import HostVarsVars, HostVars

from ._access import AnsibleAccessContext
from ._jinja_common import Marker, _TemplateConfig
from ._utils import TemplateContext, PASS_THROUGH_SCALAR_VAR_TYPES

if t.TYPE_CHECKING:
    from ._engine import TemplateEngine, TemplateOptions

_ANSIBLE_LAZY_TEMPLATE_SLOTS = tuple(('_templar', '_template_options'))
_ITERATOR_TYPES: t.Final = (c.Iterator, c.ItemsView, c.KeysView, c.ValuesView, range)

display = Display()


class _AnsibleLazyTemplateMixin:
    __slots__ = _NO_INSTANCE_STORAGE

    # due to the way Jinja handles globals, we may encounter things like functions/methods in hooked getitem/getattr that
    # always pass through this mixin; we want to silently ignore those types
    # NB: additional values are added at runtime by other Python modules to avoid circular imports
    _ignore_types: t.ClassVar[set[type]] = (
        set(PASS_THROUGH_SCALAR_VAR_TYPES) |
        set(Marker.concrete_subclasses) |  # vault marker is added later once it's defined
        {
            HostVars,
            HostVarsVars,
            types.FunctionType,  # DTFIX-MERGE: global functions returned from Jinja globals __getitem__ def _lookup
            types.MethodType,  # DTFIX-MERGE: ?
            functools.partial,  # triggered by TaskExecutor lookup partial injection as a template local
            range,  # range is acceptable for historical reasons, but only within templating, it is always an error during finalization
            type,  # DTFIX-MERGE: this is a broad ignore for looking up `range` via `resolve_or_missing`; is there a better way?
            type(''.startswith),  # DTFIX-MERGE: builtin_function_or_method - is there a better way to include callables so we're not playing whack-a-mole?
            TemplateModule,  # the result of a Jinja `import` directive, just pass it through
        }
    )
    _ignore_types_tuple: t.ClassVar[tuple[type, ...]] = tuple(_ignore_types)

    _dispatch_types: dict[type, type[_AnsibleLazyTemplateMixin]] = {}  # populated by __init_subclass__
    _container_types: set[type] = set()  # populated by __init_subclass__

    _templar: TemplateEngine
    _template_options: TemplateOptions | None

    @classmethod
    def _register_ignore_types(cls, *args: type) -> None:
        """Register additional types to ignore."""
        cls._ignore_types.update(args)
        cls._ignore_types_tuple = tuple(cls._ignore_types)

    def __init_subclass__(cls, **kwargs) -> None:
        tagged_type = cls.__mro__[1]
        native_type = tagged_type.__mro__[1]

        cls._dispatch_types[native_type] = cls
        cls._dispatch_types[tagged_type] = cls
        cls._ignore_types.add(cls)
        cls._container_types.add(native_type)
        cls._empty_tags_as_native = False  # never revert to the native type when no tags remain

    def __init__(self, contents: t.Iterable | types.EllipsisType | _LazyIterator) -> None:
        ctx = TemplateContext.current()

        # DTFIX-MERGE: this doesn't feel quite right; what if we had a JinjaOperationContext or something that made the object we were getitem-ing on
        #  accessible to try_create so we could see if there's an active unmask_type_names to use/propagate?
        #  if we do use TemplateOptions, we need to verify the recursion/propgation behavior is actually what we want
        if ctx.options.unmask_type_names:
            from ._engine import TemplateOptions

            self._template_options = TemplateOptions(unmask_type_names=ctx.options.unmask_type_names)
        else:
            self._template_options = None

        if isinstance(contents, _LazyIterator):
            self._templar = contents.templar
        elif isinstance(contents, _AnsibleLazyTemplateMixin):
            self._templar = contents._templar
        else:
            self._templar = ctx.templar  # pylint: disable=assigning-non-slot  # slot defined in derived type

    def __reduce_ex__(self, protocol):
        raise NotImplementedError("Pickling of Ansible lazy objects is not permitted.")

    @staticmethod
    def _try_create(item: t.Any, auto_template: bool = True) -> t.Any:
        """
        If `item` is a container type which supports lazy access and/or templating, return a lazy wrapped version -- otherwise return it as-is.
        When returning as-is, a warning or error may be generated for unknown types.
        The `auto_template` argument should be set to `False` when `item` is sourced from a plugin instead of Ansible variable storage.
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
            lazy_values = dispatcher._lazy_values(item)

            if not auto_template:
                lazy_values = t.cast(c.Iterable, _LazyIterator(lazy_values, None))

            tags_mapping = _try_get_internal_tags_mapping(item)
            value = t.cast(AnsibleTaggedObject, dispatcher)._instance_factory(lazy_values, tags_mapping)

            return value

        with Skippable, _TemplateConfig.unsupported_variable_type_handler.handle(AnsibleVariableTypeError, skip_on_ignore=True):
            if item_type not in _AnsibleLazyTemplateMixin._ignore_types and not isinstance(item, _AnsibleLazyTemplateMixin._ignore_types_tuple):
                # DTFIX-MERGE: need a way to reliably ascend the template stack to describe the context for constant tuples
                #              we have a similar need in other locations for more than just constant tuples
                raise AnsibleVariableTypeError(obj=item)

        return item

    def _non_lazy_copy(self) -> t.Collection:
        """
        Return a non-lazy copy of this collection.
        Any remaining lazy wrapped values will be unwrapped without further processing.
        Tags on this instance will be preserved on the returned copy.
        """
        raise NotImplementedError()  # pragma: nocover

    @staticmethod
    def _lazy_values(values: t.Any, /) -> t.Iterable:
        """
        Return an iterable that wraps each of the given elements in a lazy wrapper.
        Only elements wrapped this way will receive lazy processing when retrieved from the collection.
        """
        raise NotImplementedError()  # pragma: nocover

    def _ensure_lazy_values(self) -> None:
        """Ensure that all values in the collection are properly lazified (required, abstract)."""
        raise NotImplementedError()  # pragma: nocover

    def _proxy_or_render_lazy_value(self, key: t.Any, value: t.Any) -> t.Any:
        """
        Ensure that the value is lazy-proxied or rendered, and if a key is provided, replace the original value with the result.
        """
        if type(value) is not _LazyValue:  # pylint: disable=unidiomatic-typecheck
            AnsibleAccessContext.current().access(value)
            return value

        original_value = value.value
        AnsibleAccessContext.current().access(original_value)

        if self._templar:
            new_value = self._templar.template(original_value, options=self._template_options)
        else:
            new_value = _AnsibleLazyTemplateMixin._try_create(original_value, auto_template=False)

        if new_value is not original_value:
            AnsibleAccessContext.current().access(new_value)

        if key is not NoKeySentinel:
            self._native_type.__setitem__(self, key, new_value)  # type: ignore  # pylint: disable=unnecessary-dunder-call

        return new_value


@t.final
@dataclasses.dataclass(frozen=True, slots=True)
class _LazyValue:
    """Wrapper around values to indicate lazy behavior has not yet been applied."""

    value: t.Any


class NoKeySentinel(Sentinel):
    ...


@t.final  # consumers of lazy collections rely heavily on the concrete types being final
class _AnsibleLazyTemplateDict(_AnsibleTaggedDict, _AnsibleLazyTemplateMixin):
    __slots__ = _ANSIBLE_LAZY_TEMPLATE_SLOTS

    def __init__(self, contents: t.Iterable | types.EllipsisType | _LazyIterator = ..., /, **kwargs):
        _AnsibleLazyTemplateMixin.__init__(self, contents)

        if isinstance(contents, types.EllipsisType):
            super().__init__(**kwargs)
        elif isinstance(contents, _AnsibleLazyTemplateDict):
            super().__init__(dict.items(contents), **kwargs)
        elif isinstance(contents, _LazyIterator):
            super().__init__(contents.iterator, **kwargs)
        else:
            super().__init__(contents, **kwargs)

    def get(self, key: t.Any, default: t.Any = None) -> t.Any:
        if (value := super().get(key, NoKeySentinel)) is NoKeySentinel:
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

    def _ensure_lazy_values(self):
        for key, value in super().items():
            if type(value) is not _LazyValue:  # pylint: disable=unidiomatic-typecheck
                super().__setitem__(key, _LazyValue(value))

    def setdefault(self, key, default=None, /) -> t.Any:
        if (value := self.get(key, NoKeySentinel)) is not NoKeySentinel:
            return value

        super().__setitem__(key, default)

        return default

    def items(self):
        for key, value in super().items():
            yield key, self._proxy_or_render_lazy_value(key, value)

    def values(self):
        for _key, value in self.items():
            yield value

    def pop(self, key, default=NoKeySentinel, /) -> t.Any:
        if (value := super().get(key, NoKeySentinel)) is NoKeySentinel:
            if default is NoKeySentinel:
                raise KeyError(key)

            return default

        value = self._proxy_or_render_lazy_value(NoKeySentinel, value)

        del self[key]

        return value

    def popitem(self) -> t.Any:
        try:
            key = next(reversed(self))
        except StopIteration:
            raise KeyError("popitem(): dictionary is empty")

        value = self._proxy_or_render_lazy_value(NoKeySentinel, self[key])

        del self[key]

        return key, value

    def _native_copy(self) -> dict:
        return dict(self.items())

    @staticmethod
    def _item_source(value: dict) -> dict | _LazyIterator:
        if isinstance(value, _AnsibleLazyTemplateDict):
            return _LazyIterator(dict.items(value), value._templar)

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
    def _lazy_values(values: dict, /) -> t.Generator:
        yield from ((k, _LazyValue(v)) for k, v in values.items())

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
        # Both sides end up going through _proxy_or_render_lazy_value, so there's no Templar preservation needed.
        # In the future this could be made more lazy when both Templar instances are the same, or if per-value Templar tracking was used.
        return _AnsibleLazyTemplateDict(super().__or__(other))

    def __ror__(self, other):
        # Both sides end up going through _proxy_or_render_lazy_value, so there's no Templar preservation needed.
        # In the future this could be made more lazy when both Templar instances are the same, or if per-value Templar tracking was used.
        return _AnsibleLazyTemplateDict(super().__ror__(other))

    def __deepcopy__(self, memo):
        # DTFIX-MERGE: implement lazy deep copy
        raise NotImplementedError("Deep copy of Ansible lazy types is not supported.")


class _LazyIterator:
    # DTFIX-MERGE: better way to smuggle this state around without this wrapper?
    def __init__(self, iterator: t.Iterable, templar: TemplateEngine | None) -> None:
        self.iterator = iterator
        self.templar = templar


@t.final  # consumers of lazy collections rely heavily on the concrete types being final
class _AnsibleLazyTemplateList(_AnsibleTaggedList, _AnsibleLazyTemplateMixin):
    __slots__ = _ANSIBLE_LAZY_TEMPLATE_SLOTS

    def __init__(self, contents: t.Iterable | types.EllipsisType | _LazyIterator = ..., /):
        _AnsibleLazyTemplateMixin.__init__(self, contents)

        if isinstance(contents, types.EllipsisType):
            super().__init__()
        elif isinstance(contents, _AnsibleLazyTemplateList):
            super().__init__(list.__iter__(contents))
        elif isinstance(contents, _LazyIterator):
            super().__init__(contents.iterator)
        else:
            super().__init__(contents)

    def __getitem__(self, key: t.SupportsIndex | slice, /) -> t.Any:
        if type(key) is slice:  # pylint: disable=unidiomatic-typecheck
            return _AnsibleLazyTemplateList(_LazyIterator(super().__getitem__(key), self._templar))

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

        value = self._proxy_or_render_lazy_value(NoKeySentinel, value)

        del self[idx]

        return value

    def __str__(self):
        return str(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    def __repr__(self):
        return repr(self.copy()._native_copy())  # inefficient, but avoids mutating the current instance (to make debugging practical)

    @staticmethod
    def _item_source(value: list) -> list | _LazyIterator:
        if isinstance(value, _AnsibleLazyTemplateList):
            return _LazyIterator(list.__iter__(value), value._templar)

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
    def _lazy_values(values: list, /) -> t.Generator:
        yield from (_LazyValue(v) for v in values)

    def _ensure_lazy_values(self) -> None:
        for idx, value in enumerate(super().__iter__()):
            if type(value) is not _LazyValue:  # pylint: disable=unidiomatic-typecheck
                super().__setitem__(idx, _LazyValue(value))

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
        if isinstance(other, _AnsibleLazyTemplateList) and self._templar is not other._templar:
            # with different templars, delazify both, new collection picks up the ambient templar
            self._proxy_or_render_lazy_values()

            return _AnsibleLazyTemplateList(super().__add__(other))  # other is delazified by its __iter__

        # For all other cases, the new list inherits our templar and all values stay lazy.
        # We use list.__add__ to avoid implementing all its error behavior.
        return _AnsibleLazyTemplateList(_LazyIterator(super().__add__(other), self._templar))

    def __radd__(self, other):
        if not (other_add := getattr(other, '__add__', None)):
            raise TypeError(f'unsupported operand type(s) for +: {type(other).__name__!r} and {type(self).__name__!r}') from None

        return _AnsibleLazyTemplateList(_LazyIterator(other_add(self), self._templar))

    def __mul__(self, other):
        return _AnsibleLazyTemplateList(_LazyIterator(super().__mul__(other), self._templar))

    def __rmul__(self, other):
        return _AnsibleLazyTemplateList(_LazyIterator(super().__rmul__(other), self._templar))

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
        # DTFIX-MERGE: implement lazy deep copy
        raise NotImplementedError("Deep copy of Ansible lazy types is not supported.")


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
