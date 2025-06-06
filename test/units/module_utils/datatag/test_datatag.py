from __future__ import annotations

import builtins
import collections.abc as c
import copy
import dataclasses
import datetime
import enum
import inspect
import json

import unittest.mock
import pickle
import sys

import pytest

import ansible.module_utils.compat.typing as t

from ansible.module_utils._internal._json._profiles import (
    AnsibleProfileJSONDecoder,
    AnsibleProfileJSONEncoder,
    _JSONSerializationProfile,
)

from ansible.module_utils._internal import _messages

from ansible.module_utils._internal._datatag import (
    AnsibleSerializable,
    AnsibleSerializableEnum,
    AnsibleSingletonTagBase,
    AnsibleTaggedObject,
    NotTaggableError,
    _ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES,
    _AnsibleTaggedStr,
    _empty_frozenset,
    _try_get_internal_tags_mapping,
    _EMPTY_INTERNAL_TAGS_MAPPING,
    AnsibleSerializableDataclass,
    AnsibleSerializableWrapper,
    _TAnsibleSerializable,
    _NO_INSTANCE_STORAGE, AnsibleDatatagBase,
    _tag_dataclass_kwargs,
    AnsibleTagHelper,
)
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible.module_utils.datatag import native_type_name

if sys.version_info >= (3, 9):
    from typing import get_type_hints
else:
    # 3.8 needs the typing_extensions version of get_type_hints for `include_extras`
    from typing_extensions import get_type_hints


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class ExampleSingletonTag(AnsibleSingletonTagBase):
    pass


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class AnotherExampleSingletonTag(AnsibleSingletonTagBase):
    pass


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class ExampleTagWithContent(AnsibleDatatagBase):
    content_str: str


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class ExampleTagThatPreventsPropagation(AnsibleSingletonTagBase):
    def _get_tag_to_propagate(self, src: t.Any, value: object, *, value_type: t.Optional[type] = None) -> t.Self | None:
        return None


class CopyProtocol(t.Protocol):
    def copy(self) -> t.Any:
        """Copy this instance."""


message_instances = [
    _messages.Event(msg="bla", formatted_source_context="sc"),
    _messages.EventChain(msg_reason="a", traceback_reason="b", event=_messages.Event(msg="c")),
    _messages.ErrorSummary(event=_messages.Event(msg="bla", formatted_traceback="tb")),
    _messages.WarningSummary(event=_messages.Event(msg="bla", formatted_source_context="sc", formatted_traceback="tb")),
    _messages.DeprecationSummary(event=_messages.Event(msg="bla", formatted_source_context="sc", formatted_traceback="tb"), version="1.2.3"),
    _messages.PluginInfo(resolved_name='a.b.c', type=_messages.PluginType.MODULE),
    _messages.PluginType.MODULE,
]


def assert_round_trip(original_value, round_tripped_value, via_copy=False):
    assert original_value == round_tripped_value
    assert AnsibleTagHelper.tags(original_value) == AnsibleTagHelper.tags(round_tripped_value)

    if via_copy and type(original_value) is tuple:  # pylint: disable=unidiomatic-typecheck
        # copy.copy/copy.deepcopy significantly complicate the rules for reference equality with tuple, skip the following checks for values sourced that way
        # tuple impl of __copy__ always returns the same instance, __deepcopy__ always returns the same instance if its contents are immutable
        return

    # singleton values should rehydrate as the shared singleton instance, all others should be a new instance
    if isinstance(original_value, (AnsibleSingletonTagBase, enum.Enum)):
        assert original_value is round_tripped_value
    else:
        assert original_value is not round_tripped_value


class AnsibleSerializableSet(AnsibleSerializableWrapper[set]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> set:
        return set(d['value'])

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            value=list(self._value),
        )


class AnsibleSerializableTuple(AnsibleSerializableWrapper[tuple]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> tuple:
        return tuple(d['value'])

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            value=list(self._value),
        )


class AnsibleSerializableBytes(AnsibleSerializableWrapper[bytes]):
    __slots__ = _NO_INSTANCE_STORAGE

    @classmethod
    def _from_dict(cls: t.Type[_TAnsibleSerializable], d: t.Dict[str, t.Any]) -> bytes:
        return d['value'].encode()

    def _as_dict(self) -> t.Dict[str, t.Any]:
        return dict(
            value=self._value.decode(errors='surrogateescape'),
        )


class RoundTripEverything(_JSONSerializationProfile):
    serialize_map = {}
    allowed_ansible_serializable_types = frozenset(AnsibleSerializable._known_type_map.values())

    @classmethod
    def post_init(cls, **kwargs):
        cls.serialize_map.update(AnsibleSerializableWrapper._wrapped_types)


class RoundTripEverythingEncoder(AnsibleProfileJSONEncoder):
    _profile = RoundTripEverything


class RoundTripEverythingDecoder(AnsibleProfileJSONDecoder):
    _profile = RoundTripEverything


@pytest.mark.parametrize("untaggable_instance", [None, True, False])
def test_silent_untaggable(untaggable_instance):
    post_tag = ExampleSingletonTag().tag(untaggable_instance)

    assert post_tag is untaggable_instance


def test_try_tag() -> None:
    untaggable_value = object()
    taggable_value = "Hello"

    assert ExampleSingletonTag().try_tag(untaggable_value) is untaggable_value
    assert ExampleSingletonTag.is_tagged_on(ExampleSingletonTag().try_tag(taggable_value))


def no_op() -> None:
    """No-op function."""


@pytest.mark.parametrize("untaggable_instance", [object(), no_op])
def test_fatal_untaggable(untaggable_instance):
    with pytest.raises(NotTaggableError):
        ExampleSingletonTag().tag(untaggable_instance)


def test_ensure_empty_mapping_singleton() -> None:
    assert type(_EMPTY_INTERNAL_TAGS_MAPPING)() is _EMPTY_INTERNAL_TAGS_MAPPING
    assert copy.copy(_EMPTY_INTERNAL_TAGS_MAPPING) is _EMPTY_INTERNAL_TAGS_MAPPING
    assert copy.deepcopy(_EMPTY_INTERNAL_TAGS_MAPPING) is _EMPTY_INTERNAL_TAGS_MAPPING


def test_get_tags_mapping_from_magicmock() -> None:
    assert _try_get_internal_tags_mapping(unittest.mock.MagicMock()) is _EMPTY_INTERNAL_TAGS_MAPPING


def test_unexpected_reduce_type() -> None:
    with pytest.raises(TypeError):
        ExampleSingletonTag().tag("")._reduce("str")  # type: ignore


_str_override_method_args: t.Dict[str, t.Tuple[tuple, t.Dict[str, t.Any]]] = {
    'partition': ((' ',), {}),
    'removeprefix': ((' ',), {}),
    'removesuffix': ((' ',), {}),
}


def test_tag_types() -> None:
    value = ExampleSingletonTag().tag(AnotherExampleSingletonTag().tag("hi"))

    assert AnsibleTagHelper.tag_types(value) == {ExampleSingletonTag, AnotherExampleSingletonTag}
    assert AnsibleTagHelper.tag_types("hi") is _empty_frozenset


def test_deprecated_invalid_date_type() -> None:
    with pytest.raises(TypeError):
        Deprecated(msg="test", date=42)  # type: ignore


def test_tag_with_invalid_tag_type() -> None:
    with pytest.raises(TypeError):
        AnsibleTagHelper.tag("", ["not a tag"])  # type: ignore


def test_tag_value_type_specified_untagged() -> None:
    value = AnsibleTagHelper.tag(iter((1, 2, 3)), tuple(), value_type=list)

    assert isinstance(value, list)
    assert value == [1, 2, 3]


@dataclasses.dataclass(frozen=True)
class ContainerTestCase:
    """A test case for a container type, either using or not using a generator to source the value."""

    type_under_test: type
    use_generator: bool


class Later:
    def __init__(self, ns: dict, parent_type: type | None = None):
        self._ns = ns
        self._parent_type = parent_type

    def __getattr__(self, item):
        if item in self._ns or hasattr(self._parent_type, item) or self._ns.get('__annotations__', {}).get(item):
            return item

        raise AttributeError(item)


def _default_id_func(obj: object) -> str:
    if type(obj).__name__ == 'EncryptedString':
        return 'EncryptedString'

    res = str(obj)

    if "genexpr" in res:
        res = "(with generator)"

    return res


if sys.version_info < (3, 10):
    # deprecated: description='ditch zip(strict) polyfill' python_version='3.10'
    def zip(*args, **_kwargs):
        return builtins.zip(*args)


@dataclasses.dataclass(frozen=True)
class ParamDesc:
    names: t.List[str]
    id_func: t.Callable[[t.Any], str] = _default_id_func

    @classmethod
    def get_paramdesc_from_hint(cls, annot) -> ParamDesc:
        if annot:
            for meta in getattr(annot, '__metadata__', []):
                if isinstance(meta, ParamDesc):
                    return meta

        return ParamDesc(names=[])

    @classmethod
    def get_test_param_values(
        cls,
        obj: t.Any,
        name: str,
        maybe_with_names: t.Iterable[str],
    ) -> tuple[t.Sequence[str], t.Iterable[t.Any], t.Callable[[object], str]]:
        value = getattr(obj, name)

        try:
            if inspect.ismethod(value):
                annot = get_type_hints(value, include_extras=True).get('return')
                value = value()
            else:
                annot = get_type_hints(obj, include_extras=True).get(name)
        except Exception as ex:
            raise Exception(f"failed getting type hints for {obj!r} {name!r}") from ex

        paramdesc = cls.get_paramdesc_from_hint(annot)

        if not paramdesc.names:
            paramdesc = dataclasses.replace(paramdesc, names=["value"])

        col_count = len(paramdesc.names)

        if col_count == 1:
            col_count = 0  # HACK: don't require a wrapper container around single-element rows

        maybe_with_names = set(maybe_with_names)

        # simulate ordered set with no-values dict; the output order is not important but must be consistent per-row; use the input data order for now
        matched_names = {n: None for n in paramdesc.names}

        if not matched_names:
            return [], [], str

        out_values = []

        # DTFIX-FUTURE: apply internal tagging/annotation to point at the source data row on test failure/error?
        for rownum, row in enumerate(value or []):
            if col_count:
                # validate column count and filter the args, returning them in `matched_names` order
                if len(row) != col_count:
                    raise ValueError(f"row {rownum} of {name!r} must contain exactly {col_count} value(s); found {len(row)}")

                out_values.append([argvalue for argname, argvalue in zip(paramdesc.names, row, strict=True) if argname in matched_names])
            else:
                # just return the entire row as "value"
                out_values.append([row])

        return list(matched_names), out_values, paramdesc.id_func


class AutoParamSupport:
    def pytest_generate_tests(self, metafunc: pytest.Metafunc):
        for node, mark in metafunc.definition.iter_markers_with_node("autoparam"):
            attrname = mark.args[0]
            test_arg_names = set(inspect.signature(metafunc.function).parameters)
            argnames, argvalues, id_func = ParamDesc.get_test_param_values(metafunc.cls, attrname, test_arg_names)
            if argnames:
                metafunc.parametrize(argnames, argvalues, ids=id_func)

    def __init_subclass__(cls, **kwargs):
        cls.post_init()

    @classmethod
    def post_init(cls) -> None:
        ...


class TestDatatagTarget(AutoParamSupport):
    later = t.cast(t.Self, Later(locals()))

    tag_instances_with_reprs: t.Annotated[t.List[t.Tuple[AnsibleDatatagBase, str]], ParamDesc(["value", "expected_repr"])] = [
        (Deprecated(msg="hi mom, I am deprecated", date='2023-01-02', version="42.42"),
         "Deprecated(msg='hi mom, I am deprecated', date='2023-01-02', version='42.42')"),
        (Deprecated(msg="minimal"), "Deprecated(msg='minimal')")
    ]

    taggable_container_instances: t.List[c.Collection] = [
        dict(hi="mom"),
        ['hi', 'mom'],
        {'hi mom'},  # kept as a single item set to allow repr() testing without worrying about non-deterministic order of set items
        ("hi", "mom",),
    ]

    taggable_instances: t.List[object] = taggable_container_instances + [
        b'hi mom',
        42.0,
        42,
        "hi mom",
        datetime.datetime(2023, 9, 15, 21, 5, 30, 1900, datetime.timezone.utc),
        datetime.date(2023, 9, 15),
        datetime.time(21, 5, 30, 1900),
    ]

    tagged_object_instances: t.List[AnsibleTaggedObject] = [
        t.cast(AnsibleTaggedObject, ExampleTagWithContent(content_str=__file__).tag(item)) for item in taggable_instances]

    datatag_instances: t.List[AnsibleDatatagBase]
    serializable_instances: t.List[object]
    serializable_instances_with_instance_copy: t.List[CopyProtocol]
    serializable_types: t.List[t.Type[AnsibleSerializable]]

    @classmethod
    def post_init(cls) -> None:
        cls.datatag_instances = [value for value, _repr in cls.tag_instances_with_reprs]
        cls.serializable_instances = [value for value in (
            cls.datatag_instances + cls.tagged_object_instances + message_instances) if cls.is_type_applicable(value)]
        cls.serializable_instances_with_instance_copy = [t.cast(CopyProtocol, item) for item in cls.serializable_instances if hasattr(item, 'copy')]
        # NOTE: this doesn't include the lazy template types, those are tested separately
        cls.serializable_types = [value for value in (
            list(AnsibleSerializable._known_type_map.values()) + [AnsibleSerializable]) if cls.is_type_applicable(value)]

    @classmethod
    def is_type_applicable(cls, type_obj) -> bool:
        return (
            type_obj.__module__ != __name__ and  # exclude test-only tags/objects
            cls.is_controller_only_type(type_obj) == cls.is_controller_only_test()
        )

    @staticmethod
    def is_controller_only_type(type_obj: type) -> bool:
        return 'module_utils' not in type_obj.__module__

    @classmethod
    def is_controller_only_test(cls) -> bool:
        return cls.is_controller_only_type(cls)

    @classmethod
    def container_test_cases(cls) -> t.Annotated[t.List[t.Tuple[t.Any, t.Optional[type], type]], ParamDesc(["value", "value_type", "type_under_test"])]:
        """
        Return container test parameters for the given test case.
        Called during each test run to create the test value on-demand.
        """

        test_cases = []

        for test_case in create_container_test_cases(_ANSIBLE_ALLOWED_NON_SCALAR_COLLECTION_VAR_TYPES):
            instances = cls.taggable_instances + cls.tagged_object_instances

            # pylint: disable=unidiomatic-typecheck
            candidates = [instance for instance in instances if type(instance) is test_case.type_under_test]

            assert len(candidates) == 1, f"container_test_parameters found {len(candidates)}, expected 1"

            value = candidates[0]

            test_cases.append(create_container_test_parameters(test_case, value))

        return test_cases

    @pytest.mark.autoparam(later.tag_instances_with_reprs)
    def test_tag_repr(self, value: t.Any, expected_repr: str):
        assert repr(value) == expected_repr

    @pytest.mark.autoparam(later.container_test_cases)
    def test_tag_copy(self, value: t.Collection, value_type: type | None, type_under_test: type) -> None:
        """Ensure copying tags returns the correct type and tags."""
        tag = ExampleSingletonTag()
        src = tag.tag("tagged")

        result: t.Collection = AnsibleTagHelper.tag_copy(src, value, value_type=value_type)

        assert isinstance(result, type_under_test)
        assert tag in AnsibleTagHelper.tags(result)

    @pytest.mark.autoparam(later.taggable_instances)
    @pytest.mark.allow_delazify  # this test requires a working templar on lazies
    def test_dir(self, value: object) -> None:
        """Ensure the dir() of a tagged instance is identical to the dir() returned by the underlying native Python type, excluding `_` prefixed names."""
        tagged_instance = ExampleSingletonTag().tag(value)

        assert tagged_instance is not value
        assert ([name for name in dir(tagged_instance) if not name.startswith('_')] ==
                [name for name in dir(AnsibleTagHelper.as_native_type(tagged_instance)) if not name.startswith('_')])

    @pytest.mark.autoparam(later.taggable_instances)
    @pytest.mark.allow_delazify  # this test requires a working templar on lazies
    def test_repr(self, value: object) -> None:
        """Ensure the repr() of a tagged instance is identical to the repr() returned by the underlying native Python type."""
        tagged_instance = ExampleSingletonTag().tag(value)

        assert tagged_instance is not value
        assert repr(tagged_instance) == repr(value)

    @pytest.mark.autoparam(later.taggable_instances)
    @pytest.mark.allow_delazify  # this test requires a working templar on lazies
    def test_str(self, value: object) -> None:
        """Ensure the str() of a tagged instance is identical to the str() returned by the underlying native Python type."""
        tagged_instance = ExampleSingletonTag().tag(value)

        assert tagged_instance is not value
        assert str(tagged_instance) == str(value)

    def test_serializable_instances_cover_all_concrete_impls(self):
        tested_types = {type(instance_type) for instance_type in self.serializable_instances}

        excluded_type_names = {
            AnsibleTaggedObject.__name__,  # base class, cannot be abstract
            AnsibleSerializableDataclass.__name__,  # base class, cannot be abstract
            AnsibleSerializable.__name__,  # base class, cannot be abstract
            AnsibleSerializableEnum.__name__,  # base class, cannot be abstract
            # these types are all controller-only, so it's easier to have static type names instead of importing them
            'JinjaConstTemplate',  # serialization not required
            '_EncryptedSource',  # serialization not required
            'CapturedErrorSummary',  # serialization not required
        }

        # don't require instances for types marked abstract or types that are clearly intended to be so (but can't be marked as such)
        required_types = {instance_type for instance_type in self.serializable_types if (
            not inspect.isabstract(instance_type) and
            not instance_type.__name__.endswith('Base') and
            'Lazy' not in instance_type.__name__ and  # lazy types use the same input data
            instance_type.__name__ not in excluded_type_names and
            not issubclass(instance_type, AnsibleSerializableWrapper)
        )}

        missing_types = required_types.difference(tested_types)

        assert not missing_types

    @pytest.mark.autoparam(later.serializable_instances)
    @pytest.mark.allow_delazify  # this test requires a working templar on lazies
    def test_json_roundtrip(self, value: object):
        """
        Verify that the serialization infrastructure (profiles) can round-trip any type we choose to support.
        For taggable types which have no production use-case for round-tripping, the necessary wrapper types have been implemented in this test module.
        """
        payload = json.dumps(value, cls=RoundTripEverythingEncoder)
        round_tripped_value = json.loads(payload, cls=RoundTripEverythingDecoder)

        assert_round_trip(value, round_tripped_value)

    @pytest.mark.autoparam(later.serializable_instances)
    def test_pickle_roundtrip(self, value: object):
        if "Lazy" in type(value).__name__:
            pytest.xfail("pickle prohibited on lazies")

        pickled_value = pickle.dumps(value)
        round_tripped_value = pickle.loads(pickled_value)

        assert_round_trip(value, round_tripped_value)

    @pytest.mark.autoparam(later.serializable_instances)
    def test_deepcopy_roundtrip(self, value: object):
        if "Lazy" in type(value).__name__:
            pytest.xfail("deepcopy not supported on lazies yet")

        round_tripped_value = copy.deepcopy(value)

        # DTFIX5: ensure items in collections are copies

        assert_round_trip(value, round_tripped_value, via_copy=True)

    @pytest.mark.autoparam(later.tagged_object_instances)
    def test_native_copy(self, value: AnsibleTaggedObject) -> None:
        native_copy = value._native_copy()

        assert type(value) is not type(native_copy)
        assert isinstance(value, type(native_copy))

        if not isinstance(native_copy, int):
            assert native_copy is not value._native_copy()

        # DTFIX5: ensure items in collections are not copies

        assert native_copy == value
        assert native_copy == value._native_copy()

    @pytest.mark.autoparam(later.serializable_instances)
    def test_copy_roundtrip(self, value: object):
        if "Lazy" in type(value).__name__:
            pytest.xfail("copy prohibited on lazies")

        round_tripped_value = copy.copy(value)

        # DTFIX5: ensure items in collections are not copies

        assert_round_trip(value, round_tripped_value, via_copy=True)

    @pytest.mark.autoparam(later.serializable_instances_with_instance_copy)
    def test_instance_copy_roundtrip(self, value: CopyProtocol):
        round_tripped_value = value.copy()

        # DTFIX5: ensure items in collections are not copies

        assert_round_trip(value, round_tripped_value)

    test_dataclass_tag_base_field_validation_fail_instances: t.Annotated[
        t.List[t.Tuple[t.Type[AnsibleDatatagBase], t.Dict[str, object]]], ParamDesc(["tag_type", "init_kwargs"])
    ] = [
        (Deprecated, dict(msg=ExampleSingletonTag().tag(''))),
        (Deprecated, dict(date=ExampleSingletonTag().tag(''), msg='')),
        (Deprecated, dict(version=ExampleSingletonTag().tag(''), msg='')),
    ]

    @pytest.mark.autoparam(later.test_dataclass_tag_base_field_validation_fail_instances)
    def test_dataclass_tag_base_field_validation_fail(self, tag_type: t.Callable, init_kwargs: t.Dict[str, t.Any]) -> None:
        field_name = list(init_kwargs.keys())[0]
        actual_type = type(init_kwargs[field_name])

        with pytest.raises(TypeError, match=f"{field_name} must be <class '.*'> instead of {actual_type}"):
            tag_type(**init_kwargs)

    test_dataclass_tag_base_field_validation_pass_instances: t.Annotated[
        t.List[t.Tuple[t.Type[AnsibleDatatagBase], t.Dict[str, object]]], ParamDesc(["tag_type", "init_kwargs"])
    ] = [
        (Deprecated, dict(msg='')),
        (Deprecated, dict(msg='', date='2025-01-01')),
        (Deprecated, dict(msg='', version='')),
    ]

    @pytest.mark.autoparam(later.test_dataclass_tag_base_field_validation_pass_instances)
    def test_dataclass_tag_base_field_validation_pass(self, tag_type: t.Callable, init_kwargs: t.Dict[str, t.Any]) -> None:
        tag_type(**init_kwargs)

    @pytest.mark.autoparam(later.taggable_instances)
    @pytest.mark.allow_delazify  # this test requires a working templar on lazies
    def test_as_untagged_type(self, value: object) -> None:
        """
        Ensure that `as_untagged_type` preserves object reference identity for untagged inputs, and
        that tagged inputs are returned as their original native types.
        """
        tagged_instance = ExampleSingletonTag().tag(value)
        roundtripped_instance = AnsibleTagHelper.as_native_type(tagged_instance)

        if not isinstance(value, AnsibleTaggedObject):  # lazies are always a tagged type, so as_untagged_type will be a copy
            assert AnsibleTagHelper.as_native_type(value) is value
            assert type(roundtripped_instance) is type(value)

        assert roundtripped_instance == value

    @pytest.mark.autoparam(later.taggable_instances)
    def test_untag(self, value: object) -> None:
        """Ensure tagging and then untagging a taggable instance returns new instances as appropriate, with the correct tags and type."""
        tagged_instance = ExampleSingletonTag().tag(AnotherExampleSingletonTag().tag(value))

        tags_unchanged = Deprecated.untag(tagged_instance)  # not tagged with this value, nothing to do

        assert tags_unchanged is tagged_instance

        one_less_tag = AnotherExampleSingletonTag.untag(tagged_instance)

        assert one_less_tag is not tagged_instance
        assert type(one_less_tag) is type(tagged_instance)  # pylint: disable=unidiomatic-typecheck
        assert AnsibleTagHelper.tags(one_less_tag) == frozenset((ExampleSingletonTag(),))

        no_tags = ExampleSingletonTag.untag(one_less_tag)

        assert no_tags is not one_less_tag
        assert type(no_tags) is type(value)
        assert AnsibleTagHelper.tags(no_tags) is _empty_frozenset

        still_no_tags = ExampleSingletonTag.untag(no_tags)

        assert still_no_tags is no_tags

    @pytest.mark.autoparam(later.serializable_types)
    def test_slots(self, value: type) -> None:
        """Assert that __slots__ are properly defined on the given serializable type."""
        if value in (AnsibleSerializable, AnsibleTaggedObject):
            expect_slots = True  # non-dataclass base types have no attributes, but still use slots
        elif issubclass(value, (int, bytes, tuple, enum.Enum)):
            # non-empty slots are not supported by these variable-length data types
            # see: https://docs.python.org/3/reference/datamodel.html
            expect_slots = False
        elif issubclass(value, AnsibleSerializableDataclass) or value == AnsibleSerializableDataclass:
            assert dataclasses.is_dataclass(value)  # everything extending AnsibleSerializableDataclass must be a dataclass
            expect_slots = sys.version_info >= (3, 10)  # 3.10+ dataclasses have attributes (and support slots)
        else:
            expect_slots = True  # normal types have attributes (and slots)

        # check for slots on the type itself, ignoring slots on parents
        has_slots = '__slots__' in value.__dict__
        assert has_slots == expect_slots

        # instances of concrete types using __slots__ should not have __dict__ (which would indicate missing __slots__ definitions in the class hierarchy)
        serializable_instance = {type(instance): instance for instance in self.serializable_instances}.get(value)

        if serializable_instance:
            has_dict = hasattr(serializable_instance, '__dict__')
            assert has_dict != expect_slots

    #

    # WORKING
    @pytest.mark.autoparam(later.container_test_cases)
    def test_tag(self, value: object, value_type: type | None, type_under_test: type) -> None:
        """Ensure tagging a value returns the correct type and tags."""

        tag = ExampleSingletonTag()

        result: t.Collection = AnsibleTagHelper.tag(value, tags=tag, value_type=value_type)  # type: ignore[arg-type]

        assert isinstance(result, type_under_test)
        assert tag in AnsibleTagHelper.tags(result)


def create_container_test_parameters(test_case: ContainerTestCase, value: t.Any) -> t.Tuple[t.Any, t.Optional[type], type]:
    """
    Return container test parameters for the given test case and collection instance.
    The result is tuple of three values:
    - 1) The value or a generator.
    - 2) The type represented by the generator, or None when not using a generator.
    - 3) The type represented by the value.
    """
    if test_case.use_generator:
        # This test creates a generator to source items from the value to facilitate optimized creation of collections when tagging and copying tags.
        # To avoid triggering special behavior during iteration, a native copy is used when the value is a tagged object.

        if isinstance(value, AnsibleTaggedObject):
            native_value = value._native_copy()
        else:
            native_value = value

        if isinstance(value, c.Mapping):
            generator = ((k, v) for k, v in native_value.items())
        else:
            generator = (item for item in native_value)

        return generator, test_case.type_under_test, test_case.type_under_test  # testing via a generator, which requires use of value_type

    return value, None, test_case.type_under_test  # testing the actual type without specifying value_type


def create_container_test_cases(types: t.Iterable[t.Type[t.Collection]]) -> t.List[ContainerTestCase]:
    """
    Return a list of test cases for the given types.
    Each type will result in two test cases, one that uses a generator and one that does not.
    """
    sources: list[ContainerTestCase] = []

    for type_under_test in sorted(types, key=lambda item: item.__name__):
        sources.extend((
            ContainerTestCase(type_under_test, False),  # testing the actual type without specifying value_type
            ContainerTestCase(type_under_test, True),  # testing via a generator, which requires use of value_type
        ))

    return sources


@pytest.mark.parametrize("value, expected_type_name", (
    (1, 'int'),
    (ExampleSingletonTag().tag(1), 'int'),
    (str, 'str'),
    (_AnsibleTaggedStr, 'str'),
))
def test_friendly_name(value: object, expected_type_name: str) -> None:
    assert native_type_name(value) == expected_type_name


def test_deserialize_unknown_type() -> None:
    with pytest.raises(ValueError):
        AnsibleSerializable._deserialize({AnsibleSerializable._TYPE_KEY: 'bogus'})


def test_conflicting_tagged_type_map_entry():
    def create_problem():
        class SecondaryDict(dict, AnsibleTaggedObject):
            pass

        return SecondaryDict()  # pragma: nocover

    with pytest.raises(TypeError, match="Cannot define type 'SecondaryDict' since '_AnsibleTaggedDict' already extends 'dict'."):
        create_problem()


@pytest.mark.parametrize("value,expected_idx", (
    (('a', ExampleSingletonTag().tag('b'), ExampleSingletonTag().tag('c')), 1),
    ((ExampleSingletonTag().tag('a'), ExampleSingletonTag().tag('b'), 'c'), 0),
    ((ExampleTagWithContent(content_str='').tag('a'), 'b'), None),
))
def test_first_tagged_on(value: c.Sequence, expected_idx: int | None):
    expected = value[expected_idx] if expected_idx is not None else None

    assert ExampleSingletonTag.first_tagged_on(*value) is expected


class NonNativeTaggedType(AnsibleTaggedObject):
    """A surrogate test type that allows empty tags."""
    __slots__ = ('_ansible_tags_mapping', '_value')
    _empty_tags_as_native: t.ClassVar[bool] = False

    _value: str

    def __init__(self, value: str):
        self._ansible_tags_mapping = _EMPTY_INTERNAL_TAGS_MAPPING


def test_helper_untag():
    """Validate the behavior of the `AnsibleTagHelper.untag` method."""
    value = AnsibleTagHelper.tag("value", tags=[ExampleSingletonTag(), ExampleTagWithContent(content_str="blah")])
    assert len(AnsibleTagHelper.tag_types(value)) == 2

    less_est = AnsibleTagHelper.untag(value, ExampleSingletonTag)
    assert AnsibleTagHelper.tag_types(less_est) == {ExampleTagWithContent}

    no_tags_explicit = AnsibleTagHelper.untag(value, ExampleSingletonTag, ExampleTagWithContent)
    assert type(no_tags_explicit) is str  # pylint: disable=unidiomatic-typecheck

    no_tags_implicit = AnsibleTagHelper.untag(value)
    assert type(no_tags_implicit) is str  # pylint: disable=unidiomatic-typecheck

    untagged_value = "not a tagged value"
    assert AnsibleTagHelper.untag(untagged_value) is untagged_value

    tagged_empty_tags_ok_value = ExampleSingletonTag().tag(NonNativeTaggedType("blah"))
    untagged_empty_tags_ok_value = AnsibleTagHelper.untag(tagged_empty_tags_ok_value)
    assert type(untagged_empty_tags_ok_value) is NonNativeTaggedType  # pylint: disable=unidiomatic-typecheck
    assert not AnsibleTagHelper.tags(untagged_empty_tags_ok_value)


def test_serializable_dataclass_with_tuple() -> None:
    """Validate that dataclass deserialization converts inbound lists for tuple-typed fields."""
    @dataclasses.dataclass(**_tag_dataclass_kwargs)
    class HasTuple(AnsibleSerializableDataclass):
        data: t.Tuple[str, ...]

    assert HasTuple._from_dict(dict(data=["abc", "def"])) == HasTuple(data=("abc", "def"))


def test_tag_copy_non_propagation() -> None:
    value = ExampleTagThatPreventsPropagation().tag("hello")
    copied_value = AnsibleTagHelper.tag_copy(value, "copy")

    assert type(copied_value) is str  # pylint: disable=unidiomatic-typecheck
    assert copied_value == "copy"
