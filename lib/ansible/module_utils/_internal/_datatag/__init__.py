from __future__ import annotations

import abc
import collections.abc as c
import copy
import dataclasses
import datetime
import enum
import inspect
import sys

from itertools import chain

# deprecated: description='typing.Self exists in Python 3.11+' python_version='3.10'
from ansible.module_utils.compat import typing as t

from ansible.module_utils._internal import _dataclass_validation
from ansible.module_utils._internal._patches import _sys_intern_patch, _socket_patch

_sys_intern_patch.SysInternPatch.patch()
_socket_patch.GetAddrInfoPatch.patch()  # DTFIX-FUTURE: consider replacing this with a socket import shim that installs the patch

if sys.version_info >= (3, 10):
    # Using slots for reduced memory usage and improved performance.
    _tag_dataclass_kwargs = dict(frozen=True, repr=False, kw_only=True, slots=True)
else:
    # deprecated: description='always use dataclass slots and keyword-only args' python_version='3.9'
    _tag_dataclass_kwargs = dict(frozen=True, repr=False)

_T = t.TypeVar('_T')
_TAnsibleSerializable = t.TypeVar('_TAnsibleSerializable', bound='AnsibleSerializable')
_TAnsibleDatatagBase = t.TypeVar('_TAnsibleDatatagBase', bound='AnsibleDatatagBase')
_TAnsibleTaggedObject = t.TypeVar('_TAnsibleTaggedObject', bound='AnsibleTaggedObject')

_NO_INSTANCE_STORAGE = t.cast(t.Tuple[str], tuple())
_ANSIBLE_TAGGED_OBJECT_SLOTS = tuple(('_ansible_tags_mapping',))

# shared empty frozenset for default values
_empty_frozenset: t.FrozenSet = frozenset()

# Technical Notes
#
# Tagged values compare (and thus hash) the same as their base types, so a value that differs only by its tags will appear identical to non-tag-aware code.
# This will affect storage and update of tagged values in dictionary keys, sets, etc. While tagged values can be used as keys in hashable collections,
# updating a key usually requires removal and re-addition.


class AnsibleTagHelper:
    """Utility methods for working with Ansible data tags."""

    @staticmethod
    def untag(value: _T, *tag_types: t.Type[AnsibleDatatagBase]) -> _T:
        """
        If tags matching any of `tag_types` are present on `value`, return a copy with those tags removed.
        If no `tag_types` are specified and the object has tags, return a copy with all tags removed.
        Otherwise, the original `value` is returned.
        """
        tag_set = AnsibleTagHelper.tags(value)

        if not tag_set:
            return value

        if tag_types:
            tags_mapping = _AnsibleTagsMapping((type(tag), tag) for tag in tag_set if type(tag) not in tag_types)  # pylint: disable=unidiomatic-typecheck

            if len(tags_mapping) == len(tag_set):
                return value  # if no tags were removed, return the original instance
        else:
            tags_mapping = None

        if not tags_mapping:
            if t.cast(AnsibleTaggedObject, value)._empty_tags_as_native:
                return t.cast(AnsibleTaggedObject, value)._native_copy()

            tags_mapping = _EMPTY_INTERNAL_TAGS_MAPPING

        tagged_type = AnsibleTaggedObject._get_tagged_type(type(value))

        return t.cast(_T, tagged_type._instance_factory(value, tags_mapping))

    @staticmethod
    def tags(value: t.Any) -> t.FrozenSet[AnsibleDatatagBase]:
        tags = _try_get_internal_tags_mapping(value)

        if tags is _EMPTY_INTERNAL_TAGS_MAPPING:
            return _empty_frozenset

        return frozenset(tags.values())

    @staticmethod
    def tag_types(value: t.Any) -> t.FrozenSet[t.Type[AnsibleDatatagBase]]:
        tags = _try_get_internal_tags_mapping(value)

        if tags is _EMPTY_INTERNAL_TAGS_MAPPING:
            return _empty_frozenset

        return frozenset(tags)

    @staticmethod
    def base_type(type_or_value: t.Any, /) -> type:
        """Return the friendly type of the given type or value. If the type is an AnsibleTaggedObject, the native type will be used."""
        if isinstance(type_or_value, type):
            the_type = type_or_value
        else:
            the_type = type(type_or_value)

        if issubclass(the_type, AnsibleTaggedObject):
            the_type = type_or_value._native_type

        # DTFIX-FUTURE: provide a knob to optionally report the real type for debugging purposes
        return the_type

    @staticmethod
    def as_native_type(value: _T) -> _T:
        """
        Returns an untagged native data type matching the input value, or the original input if the value was not a tagged type.
        Containers are not recursively processed.
        """
        if isinstance(value, AnsibleTaggedObject):
            value = value._native_copy()

        return value

    @staticmethod
    @t.overload
    def tag_copy(src: t.Any, value: _T) -> _T: ...  # pragma: nocover

    @staticmethod
    @t.overload
    def tag_copy(src: t.Any, value: t.Any, *, value_type: type[_T]) -> _T: ...  # pragma: nocover

    @staticmethod
    @t.overload
    def tag_copy(src: t.Any, value: _T, *, value_type: None = None) -> _T: ...  # pragma: nocover

    @staticmethod
    def tag_copy(src: t.Any, value: _T, *, value_type: t.Optional[type] = None) -> _T:
        """Return a copy of `value`, with tags copied from `src`, overwriting any existing tags of the same types."""
        src_tags = AnsibleTagHelper.tags(src)
        value_tags = [(tag, tag._get_tag_to_propagate(src, value, value_type=value_type)) for tag in src_tags]
        tags = [tag[1] for tag in value_tags if tag[1] is not None]
        tag_types_to_remove = [type(tag[0]) for tag in value_tags if tag[1] is None]

        if tag_types_to_remove:
            value = AnsibleTagHelper.untag(value, *tag_types_to_remove)

        return AnsibleTagHelper.tag(value, tags, value_type=value_type)

    @staticmethod
    @t.overload
    def tag(value: _T, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]]) -> _T: ...  # pragma: nocover

    @staticmethod
    @t.overload
    def tag(value: t.Any, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]], *, value_type: type[_T]) -> _T: ...  # pragma: nocover

    @staticmethod
    @t.overload
    def tag(value: _T, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]], *, value_type: None = None) -> _T: ...  # pragma: nocover

    @staticmethod
    def tag(value: _T, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]], *, value_type: t.Optional[type] = None) -> _T:
        """
        Return a copy of `value`, with `tags` applied, overwriting any existing tags of the same types.
        If `value` is an ignored type, or `tags` is empty, the original `value` will be returned.
        If `value` is not taggable, a `NotTaggableError` exception will be raised.
        If `value_type` was given, that type will be returned instead.
        """
        if value_type is None:
            value_type_specified = False
            value_type = type(value)
        else:
            value_type_specified = True

        # if no tags to apply, just return what we got
        # NB: this only works because the untaggable types are singletons (and thus direct type comparison works)
        if not tags or value_type in _untaggable_types:
            if value_type_specified:
                return value_type(value)

            return value

        tag_list: list[AnsibleDatatagBase]

        # noinspection PyProtectedMember
        if type(tags) in _known_tag_types:
            tag_list = [tags]  # type: ignore[list-item]
        else:
            tag_list = list(tags)  # type: ignore[arg-type]

            for idx, tag in enumerate(tag_list):
                # noinspection PyProtectedMember
                if type(tag) not in _known_tag_types:
                    # noinspection PyProtectedMember
                    raise TypeError(f'tags[{idx}] of type {type(tag)} is not one of {_known_tag_types}')

        existing_internal_tags_mapping = _try_get_internal_tags_mapping(value)

        if existing_internal_tags_mapping is not _EMPTY_INTERNAL_TAGS_MAPPING:
            # include the existing tags first so new tags of the same type will overwrite
            tag_list = list(chain(existing_internal_tags_mapping.values(), tag_list))

        tags_mapping = _AnsibleTagsMapping((type(tag), tag) for tag in tag_list)
        tagged_type = AnsibleTaggedObject._get_tagged_type(value_type)

        return t.cast(_T, tagged_type._instance_factory(value, tags_mapping))

    @staticmethod
    def try_tag(value: _T, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]]) -> _T:
        """
        Return a copy of `value`, with `tags` applied, overwriting any existing tags of the same types.
        If `value` is not taggable or `tags` is empty, the original `value` will be returned.
        """
        try:
            return AnsibleTagHelper.tag(value, tags)
        except NotTaggableError:
            return value


class AnsibleSerializable:
    __slots__ = _NO_INSTANCE_STORAGE

    _known_type_map: t.ClassVar[t.Dict[str, t.Type['AnsibleSerializable']]] = {}
    _TYPE_KEY: t.ClassVar[str] = '__ansible_type'

    _type_key: t.ClassVar[str]

    def __init_subclass__(cls, **kwargs) -> None:
        # this is needed to call __init__subclass__ on mixins for derived types
        super().__init_subclass__(**kwargs)

        cls._type_key = cls.__name__

        # DTFIX-FUTURE: is there a better way to exclude non-abstract types which are base classes?
        if not inspect.isabstract(cls) and not cls.__name__.endswith('Base') and cls.__name__ != 'AnsibleTaggedObject':
            AnsibleSerializable._known_type_map[cls._type_key] = cls

    @classmethod
    @abc.abstractmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> object:
        """Return an instance of this type, created from the given dictionary."""

    @abc.abstractmethod
    def _as_dict(self) -> t.Dict[str, t.Any]:
        """
        Return a serialized version of this instance as a dictionary.
        This operation is *NOT* recursive - the returned dictionary may still include custom types.
        It is the responsibility of the caller to handle recursion of the returned dict.
        """

    def _serialize(self) -> t.Dict[str, t.Any]:
        value = self._as_dict()
        value.update({AnsibleSerializable._TYPE_KEY: self._type_key})

        return value

    @staticmethod
    def _deserialize(data: t.Dict[str, t.Any]) -> object:
        """Deserialize an object from the supplied data dict, which will be mutated if it contains a type key."""
        type_name = data.pop(AnsibleSerializable._TYPE_KEY, ...)  # common usage assumes `data` is an intermediate dict provided by a deserializer

        if type_name is ...:
            return None

        type_value = AnsibleSerializable._known_type_map.get(type_name)

        if not type_value:
            raise ValueError(f'An unknown {AnsibleSerializable._TYPE_KEY!r} value {type_name!r} was encountered during deserialization.')

        return type_value._from_dict(data)

    def _repr(self, name: str) -> str:
        args = self._as_dict()
        arg_string = ', '.join((f'{k}={v!r}' for k, v in args.items()))
        return f'{name}({arg_string})'


class AnsibleSerializableEnum(AnsibleSerializable, enum.Enum):
    """Base class for serializable enumerations."""

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(value=self.value)

    @classmethod
    def _from_dict(cls, d: t.Dict[str, t.Any]) -> t.Self:
        return cls(d['value'].lower())

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}.{self.name}>'

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class AnsibleSerializableWrapper(AnsibleSerializable, t.Generic[_T], metaclass=abc.ABCMeta):
    __slots__ = ('_value',)

    _wrapped_types: t.ClassVar[dict[type, type[AnsibleSerializable]]] = {}
    _wrapped_type: t.ClassVar[type] = type(None)

    def __init__(self, value: _T) -> None:
        self._value: _T = value

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls._wrapped_type = t.get_args(cls.__orig_bases__[0])[0]
        cls._wrapped_types[cls._wrapped_type] = cls


class AnsibleSerializableDate(AnsibleSerializableWrapper[datetime.date]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> datetime.date:
        return datetime.date.fromisoformat(d['iso8601'])

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            iso8601=self._value.isoformat(),
        )


class AnsibleSerializableTime(AnsibleSerializableWrapper[datetime.time]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> datetime.time:
        value = datetime.time.fromisoformat(d['iso8601'])
        value.replace(fold=d['fold'])

        return value

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            iso8601=self._value.isoformat(),
            fold=self._value.fold,
        )


class AnsibleSerializableDateTime(AnsibleSerializableWrapper[datetime.datetime]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> datetime.datetime:
        value = datetime.datetime.fromisoformat(d['iso8601'])
        value.replace(fold=d['fold'])

        return value

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            iso8601=self._value.isoformat(),
            fold=self._value.fold,
        )


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class AnsibleSerializableDataclass(AnsibleSerializable, metaclass=abc.ABCMeta):
    _validation_allow_subclasses = True
    _validation_auto_enabled = True

    def _as_dict(self) -> t.Dict[str, t.Any]:
        # omit None values when None is the field default
        # DTFIX-FUTURE: this implementation means we can never change the default on fields which have None for their default
        #          other defaults can be changed -- but there's no way to override this behavior either way for other default types
        #          it's a trip hazard to have the default logic here, rather than per field (or not at all)
        #          consider either removing the filtering or requiring it to be explicitly set per field using dataclass metadata
        fields = ((field, getattr(self, field.name)) for field in dataclasses.fields(self))
        return {field.name: value for field, value in fields if value is not None or field.default is not None}

    @classmethod
    def _from_dict(cls, d: t.Dict[str, t.Any]) -> t.Self:
        # DTFIX-FUTURE: optimize this to avoid the dataclasses fields metadata and get_origin stuff at runtime
        type_hints = t.get_type_hints(cls)
        mutated_dict: dict[str, t.Any] | None = None

        for field in dataclasses.fields(cls):
            if t.get_origin(type_hints[field.name]) is tuple:  # NOTE: only supports bare tuples, not optional or inside a union
                if type(field_value := d.get(field.name)) is list:  # pylint: disable=unidiomatic-typecheck
                    if mutated_dict is None:
                        mutated_dict = d.copy()

                    mutated_dict[field.name] = tuple(field_value)

        return cls(**(mutated_dict or d))

    def __init_subclass__(cls, **kwargs) -> None:
        super(AnsibleSerializableDataclass, cls).__init_subclass__(**kwargs)  # cannot use super() without arguments when using slots

        if cls._validation_auto_enabled:
            try:
                _dataclass_validation.inject_post_init_validation(cls, cls._validation_allow_subclasses)  # code gen a real __post_init__ method
            except Exception as ex:
                raise Exception(f'Validation code generation failed on {cls}.') from ex


class Tripwire:
    """Marker mixin for types that should raise an error when encountered."""

    __slots__ = _NO_INSTANCE_STORAGE

    def trip(self) -> t.NoReturn:
        """Derived types should implement a failure behavior."""
        raise NotImplementedError()


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class AnsibleDatatagBase(AnsibleSerializableDataclass, metaclass=abc.ABCMeta):
    """
    Base class for data tagging tag types.
    New tag types need to be considered very carefully; e.g.: which serialization/runtime contexts they're allowed in, fallback behavior, propagation.
    """

    _validation_allow_subclasses = False

    def __init_subclass__(cls, **kwargs) -> None:
        # NOTE: This method is called twice when the datatag type is a dataclass.
        super(AnsibleDatatagBase, cls).__init_subclass__(**kwargs)  # cannot use super() without arguments when using slots

        # DTFIX-FUTURE: "freeze" this after module init has completed to discourage custom external tag subclasses

        # DTFIX-FUTURE: is there a better way to exclude non-abstract types which are base classes?
        if not inspect.isabstract(cls) and not cls.__name__.endswith('Base'):
            existing = _known_tag_type_map.get(cls.__name__)

            if existing:
                # When the datatag type is a dataclass, the first instance will be the non-dataclass type.
                # It must be removed from the known tag types before adding the dataclass version.
                _known_tag_types.remove(existing)

            _known_tag_type_map[cls.__name__] = cls
            _known_tag_types.add(cls)

    @classmethod
    def is_tagged_on(cls, value: t.Any) -> bool:
        return cls in _try_get_internal_tags_mapping(value)

    @classmethod
    def first_tagged_on(cls, *values: t.Any) -> t.Any | None:
        """Return the first value which is tagged with this type, or None if no match is found."""
        for value in values:
            if cls.is_tagged_on(value):
                return value

        return None

    @classmethod
    def get_tag(cls, value: t.Any) -> t.Optional[t.Self]:
        return _try_get_internal_tags_mapping(value).get(cls)

    @classmethod
    def get_required_tag(cls, value: t.Any) -> t.Self:
        if (tag := cls.get_tag(value)) is None:
            # DTFIX-FUTURE: we really should have a way to use AnsibleError with obj in module_utils when it's controller-side
            raise ValueError(f'The type {type(value).__name__!r} is not tagged with {cls.__name__!r}.')

        return tag

    @classmethod
    def untag(cls, value: _T) -> _T:
        """
        If this tag type is present on `value`, return a copy with that tag removed.
        Otherwise, the original `value` is returned.
        """
        return AnsibleTagHelper.untag(value, cls)

    def tag(self, value: _T) -> _T:
        """
        Return a copy of `value` with this tag applied, overwriting any existing tag of the same type.
        If `value` is an ignored type, the original `value` will be returned.
        If `value` is not taggable, a `NotTaggableError` exception will be raised.
        """
        return AnsibleTagHelper.tag(value, self)

    def try_tag(self, value: _T) -> _T:
        """
        Return a copy of `value` with this tag applied, overwriting any existing tag of the same type.
        If `value` is not taggable, the original `value` will be returned.
        """
        return AnsibleTagHelper.try_tag(value, self)

    def _get_tag_to_propagate(self, src: t.Any, value: object, *, value_type: t.Optional[type] = None) -> t.Self | None:
        """
        Called by `AnsibleTagHelper.tag_copy` during tag propagation.
        Returns an instance of this tag appropriate for propagation to `value`, or `None` if the tag should not be propagated.
        Derived implementations may consult the arguments relayed from `tag_copy` to determine if and how the tag should be propagated.
        """
        return self

    def __repr__(self) -> str:
        return AnsibleSerializable._repr(self, self.__class__.__name__)


# used by the datatag Ansible/Jinja test plugin to find tags by name
_known_tag_type_map: t.Dict[str, t.Type[AnsibleDatatagBase]] = {}
_known_tag_types: t.Set[t.Type[AnsibleDatatagBase]] = set()

if sys.version_info >= (3, 9):
    # Include the key and value types in the type hints on Python 3.9 and later.
    # Earlier versions do not support subscriptable dict.
    # deprecated: description='always use subscriptable dict' python_version='3.8'
    class _AnsibleTagsMapping(dict[type[_TAnsibleDatatagBase], _TAnsibleDatatagBase]):
        __slots__ = _NO_INSTANCE_STORAGE

else:

    class _AnsibleTagsMapping(dict):
        __slots__ = _NO_INSTANCE_STORAGE


class _EmptyROInternalTagsMapping(dict):
    """
    Optimizes empty tag mapping by using a shared singleton read-only dict.
    Since mappingproxy is not pickle-able and causes other problems, we had to roll our own.
    """

    def __new__(cls):
        try:
            # noinspection PyUnresolvedReferences
            return cls._instance
        except AttributeError:
            cls._instance = dict.__new__(cls)

        # noinspection PyUnresolvedReferences
        return cls._instance

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def setdefault(self, __key, __default=None):
        raise NotImplementedError()

    def update(self, __m, **kwargs):
        raise NotImplementedError()


_EMPTY_INTERNAL_TAGS_MAPPING = t.cast(_AnsibleTagsMapping, _EmptyROInternalTagsMapping())
"""
An empty read-only mapping of tags.
Also used as a sentinel to cheaply determine that a type is not tagged by using a reference equality check.
"""


class CollectionWithMro(c.Collection, t.Protocol):
    """Used to represent a Collection with __mro__ in a TypeGuard for tools that don't include __mro__ in Collection."""

    __mro__: tuple[type, ...]


def is_non_scalar_collection_type(value: type) -> t.TypeGuard[type[CollectionWithMro]]:
    """Returns True if the value is a non-scalar collection type, otherwise returns False."""
    return issubclass(value, c.Collection) and not issubclass(value, str) and not issubclass(value, bytes)


def _try_get_internal_tags_mapping(value: t.Any) -> _AnsibleTagsMapping:
    """Return the internal tag mapping of the given value, or a sentinel value if it is not tagged."""
    # noinspection PyBroadException
    try:
        # noinspection PyProtectedMember
        tags = value._ansible_tags_mapping
    except Exception:
        # try/except is a cheap way to determine if this is a tagged object without using isinstance
        # handling Exception accounts for types that may raise something other than AttributeError
        return _EMPTY_INTERNAL_TAGS_MAPPING

    # handle cases where the instance always returns something, such as Marker or MagicMock
    if type(tags) is not _AnsibleTagsMapping:  # pylint: disable=unidiomatic-typecheck
        return _EMPTY_INTERNAL_TAGS_MAPPING

    return tags


class NotTaggableError(TypeError):
    def __init__(self, value):
        super(NotTaggableError, self).__init__('{} is not taggable'.format(value))


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class AnsibleSingletonTagBase(AnsibleDatatagBase):
    def __new__(cls):
        try:
            # noinspection PyUnresolvedReferences
            return cls._instance
        except AttributeError:
            cls._instance = AnsibleDatatagBase.__new__(cls)

        # noinspection PyUnresolvedReferences
        return cls._instance

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return {}


class AnsibleTaggedObject(AnsibleSerializable):
    __slots__ = _NO_INSTANCE_STORAGE

    _native_type: t.ClassVar[type]
    _item_source: t.ClassVar[t.Optional[t.Callable]] = None

    _tagged_type_map: t.ClassVar[t.Dict[type, t.Type['AnsibleTaggedObject']]] = {}
    _tagged_collection_types: t.ClassVar[t.Set[t.Type[c.Collection]]] = set()
    _collection_types: t.ClassVar[t.Set[t.Type[c.Collection]]] = set()

    _empty_tags_as_native: t.ClassVar[bool] = True  # by default, untag will revert to the native type when no tags remain
    _subclasses_native_type: t.ClassVar[bool] = True  # by default, tagged types are assumed to subclass the type they augment

    _ansible_tags_mapping: _AnsibleTagsMapping | _EmptyROInternalTagsMapping = _EMPTY_INTERNAL_TAGS_MAPPING
    """
    Efficient internal storage of tags, indexed by tag type.
    Contains no more than one instance of each tag type.
    This is defined as a class attribute to support type hinting and documentation.
    It is overwritten with an instance attribute during instance creation.
    The instance attribute slot is provided by the derived type.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        try:
            init_class = cls._init_class  # type: ignore[attr-defined]
        except AttributeError:
            pass
        else:
            init_class()

        if not cls._subclasses_native_type:
            return  # NOTE: When not subclassing a native type, the derived type must set cls._native_type itself and cls._empty_tags_as_native to False.

        try:
            # Subclasses of tagged types will already have a native type set and won't need to detect it.
            # Special types which do not subclass a native type can also have their native type already set.
            # Automatic item source selection is only implemented for types that don't set _native_type.
            cls._native_type
        except AttributeError:
            # Direct subclasses of native types won't have cls._native_type set, so detect the native type.
            cls._native_type = cls.__bases__[0]

            # Detect the item source if not already set.
            if cls._item_source is None and is_non_scalar_collection_type(cls._native_type):
                cls._item_source = cls._native_type.__iter__  # type: ignore[attr-defined]

        # Use a collection specific factory for types with item sources.
        if cls._item_source:
            cls._instance_factory = cls._instance_factory_collection  # type: ignore[method-assign]

        new_type_direct_subclass = cls.__mro__[1]

        conflicting_impl = AnsibleTaggedObject._tagged_type_map.get(new_type_direct_subclass)

        if conflicting_impl:
            raise TypeError(f'Cannot define type {cls.__name__!r} since {conflicting_impl.__name__!r} already extends {new_type_direct_subclass.__name__!r}.')

        AnsibleTaggedObject._tagged_type_map[new_type_direct_subclass] = cls

        if is_non_scalar_collection_type(cls):
            AnsibleTaggedObject._tagged_collection_types.add(cls)
            AnsibleTaggedObject._collection_types.update({cls, new_type_direct_subclass})

    def _native_copy(self) -> t.Any:
        """
        Returns a copy of the current instance as its native Python type.
        Any dynamic access behaviors that apply to this instance will be used during creation of the copy.
        In the case of a container type, this is a shallow copy.
        Recursive calls to native_copy are the responsibility of the caller.
        """
        return self._native_type(self)  # pylint: disable=abstract-class-instantiated

    @classmethod
    def _instance_factory(cls, value: t.Any, tags_mapping: _AnsibleTagsMapping) -> t.Self:
        # There's no way to indicate cls is callable with a single arg without defining a useless __init__.
        instance = cls(value)  # type: ignore[call-arg]
        instance._ansible_tags_mapping = tags_mapping

        return instance

    @staticmethod
    def _get_tagged_type(value_type: type) -> type[AnsibleTaggedObject]:
        tagged_type: t.Optional[type[AnsibleTaggedObject]]

        if issubclass(value_type, AnsibleTaggedObject):
            tagged_type = value_type
        else:
            tagged_type = AnsibleTaggedObject._tagged_type_map.get(value_type)

        if not tagged_type:
            raise NotTaggableError(value_type)

        return tagged_type

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            value=self._native_copy(),
            tags=list(self._ansible_tags_mapping.values()),
        )

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleTaggedObject], d: t.Dict[str, t.Any]) -> _TAnsibleTaggedObject:
        return AnsibleTagHelper.tag(**d)

    @classmethod
    def _instance_factory_collection(
        cls,
        value: t.Any,
        tags_mapping: _AnsibleTagsMapping,
    ) -> t.Self:
        if type(value) in AnsibleTaggedObject._collection_types:
            # use the underlying iterator to avoid access/iteration side effects (e.g. templating/wrapping on Lazy subclasses)
            instance = cls(cls._item_source(value))  # type: ignore[call-arg,misc]
        else:
            # this is used when the value is a generator
            instance = cls(value)  # type: ignore[call-arg]

        instance._ansible_tags_mapping = tags_mapping

        return instance

    def _copy_collection(self) -> AnsibleTaggedObject:
        """
        Return a shallow copy of this instance, which must be a collection.
        This uses the underlying iterator to avoid access/iteration side effects (e.g. templating/wrapping on Lazy subclasses).
        """
        return AnsibleTagHelper.tag_copy(self, type(self)._item_source(self), value_type=type(self))  # type: ignore[misc]

    @classmethod
    def _new(cls, value: t.Any, *args, **kwargs) -> t.Self:
        if type(value) is _AnsibleTagsMapping:  # pylint: disable=unidiomatic-typecheck
            self = cls._native_type.__new__(cls, *args, **kwargs)
            self._ansible_tags_mapping = value
            return self

        return cls._native_type.__new__(cls, value, *args, **kwargs)

    def _reduce(self, reduced: t.Union[str, tuple[t.Any, ...]]) -> tuple:
        if type(reduced) is not tuple:  # pylint: disable=unidiomatic-typecheck
            raise TypeError()

        updated: list[t.Any] = list(reduced)
        updated[1] = (self._ansible_tags_mapping,) + updated[1]

        return tuple(updated)


class _AnsibleTaggedStr(str, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS


class _AnsibleTaggedBytes(bytes, AnsibleTaggedObject):
    # nonempty __slots__ not supported for subtype of 'bytes'
    pass


class _AnsibleTaggedInt(int, AnsibleTaggedObject):
    # nonempty __slots__ not supported for subtype of 'int'
    pass


class _AnsibleTaggedFloat(float, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS


class _AnsibleTaggedDateTime(datetime.datetime, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    @classmethod
    def _instance_factory(cls, value: datetime.datetime, tags_mapping: _AnsibleTagsMapping) -> _AnsibleTaggedDateTime:
        instance = cls(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.microsecond,
            tzinfo=value.tzinfo,
            fold=value.fold,
        )

        instance._ansible_tags_mapping = tags_mapping

        return instance

    def _native_copy(self) -> datetime.datetime:
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=self.tzinfo,
            fold=self.fold,
        )

    def __new__(cls, year, *args, **kwargs):
        return super()._new(year, *args, **kwargs)

    def __reduce_ex__(self, protocol: t.SupportsIndex) -> tuple:
        return super()._reduce(super().__reduce_ex__(protocol))

    def __repr__(self) -> str:
        return self._native_copy().__repr__()


class _AnsibleTaggedDate(datetime.date, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    @classmethod
    def _instance_factory(cls, value: datetime.date, tags_mapping: _AnsibleTagsMapping) -> _AnsibleTaggedDate:
        instance = cls(
            year=value.year,
            month=value.month,
            day=value.day,
        )

        instance._ansible_tags_mapping = tags_mapping

        return instance

    def _native_copy(self) -> datetime.date:
        return datetime.date(
            year=self.year,
            month=self.month,
            day=self.day,
        )

    def __new__(cls, year, *args, **kwargs):
        return super()._new(year, *args, **kwargs)

    def __reduce__(self) -> tuple:
        return super()._reduce(super().__reduce__())

    def __repr__(self) -> str:
        return self._native_copy().__repr__()


class _AnsibleTaggedTime(datetime.time, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    @classmethod
    def _instance_factory(cls, value: datetime.time, tags_mapping: _AnsibleTagsMapping) -> _AnsibleTaggedTime:
        instance = cls(
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.microsecond,
            tzinfo=value.tzinfo,
            fold=value.fold,
        )

        instance._ansible_tags_mapping = tags_mapping

        return instance

    def _native_copy(self) -> datetime.time:
        return datetime.time(
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=self.tzinfo,
            fold=self.fold,
        )

    def __new__(cls, hour, *args, **kwargs):
        return super()._new(hour, *args, **kwargs)

    def __reduce_ex__(self, protocol: t.SupportsIndex) -> tuple:
        return super()._reduce(super().__reduce_ex__(protocol))

    def __repr__(self) -> str:
        return self._native_copy().__repr__()


class _AnsibleTaggedDict(dict, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    _item_source: t.ClassVar[t.Optional[t.Callable]] = dict.items

    def __copy__(self):
        return super()._copy_collection()

    def copy(self) -> _AnsibleTaggedDict:
        return copy.copy(self)

    # NB: Tags are intentionally not preserved for operator methods that return a new instance. In-place operators ignore tags from the `other` instance.
    # Propagation of tags in these cases is left to the caller, based on needs specific to their use case.


class _AnsibleTaggedList(list, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    def __copy__(self):
        return super()._copy_collection()

    def copy(self) -> _AnsibleTaggedList:
        return copy.copy(self)

    # NB: Tags are intentionally not preserved for operator methods that return a new instance. In-place operators ignore tags from the `other` instance.
    # Propagation of tags in these cases is left to the caller, based on needs specific to their use case.


class _AnsibleTaggedSet(set, AnsibleTaggedObject):
    __slots__ = _ANSIBLE_TAGGED_OBJECT_SLOTS

    def __copy__(self):
        return super()._copy_collection()

    def copy(self):
        return copy.copy(self)

    def __init__(self, value=None, *args, **kwargs):
        if type(value) is _AnsibleTagsMapping:  # pylint: disable=unidiomatic-typecheck
            super().__init__(*args, **kwargs)
        else:
            super().__init__(value, *args, **kwargs)

    def __new__(cls, value=None, *args, **kwargs):
        return super()._new(value, *args, **kwargs)

    def __reduce_ex__(self, protocol: t.SupportsIndex) -> tuple:
        return super()._reduce(super().__reduce_ex__(protocol))

    def __str__(self) -> str:
        return self._native_copy().__str__()

    def __repr__(self) -> str:
        return self._native_copy().__repr__()


class _AnsibleTaggedTuple(tuple, AnsibleTaggedObject):
    # nonempty __slots__ not supported for subtype of 'tuple'

    def __copy__(self):
        return super()._copy_collection()


_untaggable_types = {type(None), bool}
"""
Attempts to apply tags to values of these types will be silently ignored.
While we could proxy or subclass builtin singletons, they're idiomatically compared with "is" reference equality, which we can't customize.
This set gets augmented with additional types when some controller-only types are imported.
"""

# noinspection PyProtectedMember
_ANSIBLE_ALLOWED_VAR_TYPES = frozenset({type(None), bool}) | set(AnsibleTaggedObject._tagged_type_map) | set(AnsibleTaggedObject._tagged_type_map.values())
"""These are the exact types supported by Ansible's variable storage."""

_ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES = frozenset(item for item in _ANSIBLE_ALLOWED_VAR_TYPES if is_non_scalar_collection_type(item))
"""These are the exact non-scalar collection types supported by Ansible's variable storage."""

_ANSIBLE_ALLOWED_MAPPING_VAR_TYPES = frozenset(item for item in _ANSIBLE_ALLOWED_VAR_TYPES if issubclass(item, c.Mapping))
"""These are the exact mapping types supported by Ansible's variable storage."""

_ANSIBLE_ALLOWED_SCALAR_VAR_TYPES = _ANSIBLE_ALLOWED_VAR_TYPES - _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES
"""These are the exact scalar types supported by Ansible's variable storage."""
