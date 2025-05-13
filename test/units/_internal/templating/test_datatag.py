from __future__ import annotations

import collections.abc as c
import typing as t

import pytest

from ansible.module_utils._internal._datatag import (
    AnsibleSerializable,
    AnsibleTaggedObject,
)

# temporarily here to ensure this type is always "seen" in the known serializable types list
from ansible._internal._templating._jinja_bits import _JinjaConstTemplate  # pylint: disable=unused-import
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateMixin, _AnsibleLazyAccessTuple

from ...module_utils.datatag.test_datatag import (
    ContainerTestCase,
    create_container_test_parameters,
    TestDatatagTarget as _TestDatatagTarget, Later, ParamDesc
)


class TestDatatagTemplar(_TestDatatagTarget):
    later = t.cast(t.Self, Later(locals(), _TestDatatagTarget))

    lazy_serializable_types: t.Annotated[
        list[type[c.Collection]], ParamDesc(["lazy_type"])
    ] = list(
        t.cast(type[c.Collection], known_type) for known_type in AnsibleSerializable._known_type_map.values()
        if issubclass(known_type, _AnsibleLazyTemplateMixin)
    )

    serializable_instances: t.Annotated[list[object], ParamDesc(["non_lazy_value"])]

    taggable_container_instances: t.Annotated[list[c.Collection], ParamDesc(["non_lazy_value"])] = _TestDatatagTarget.taggable_container_instances
    taggable_instances: t.Annotated[list[object], ParamDesc(["non_lazy_value"])] = t.cast(list[object], taggable_container_instances)

    @classmethod
    def post_init(cls, **kwargs):
        cls.serializable_types = t.cast(list[type[AnsibleSerializable]], cls.lazy_serializable_types)
        cls.serializable_instances = [(obj, ) for obj in cls.taggable_container_instances]

    @classmethod
    def container_test_parameters(cls, test_case: ContainerTestCase) -> tuple[t.Any, t.Optional[type], type]:
        """
        Return container test parameters for the given test case.
        Called during each test run to create the test value on-demand.
        """
        # pylint: disable=unidiomatic-typecheck
        candidates = [instance for instance in cls.taggable_container_instances if type(instance) is test_case.type_under_test.__mro__[2]]

        assert len(candidates) == 1

        value = candidates[0]
        value = _AnsibleLazyTemplateMixin._try_create(value)

        return create_container_test_parameters(test_case, value)

    @classmethod
    def container_test_cases(cls) -> t.Annotated[list[tuple[t.Any, type]], ParamDesc(["non_lazy_value", "type_under_test"])]:  # type: ignore[override]
        # for each lazy_serializable type, find exactly one matching taggable container instance
        # create the lazy type from the instance
        out_values = []
        for type_under_test in cls.lazy_serializable_types:
            candidates = [instance for instance in cls.taggable_container_instances
                          if type(instance) is type_under_test.__mro__[2]]  # pylint: disable=unidiomatic-typecheck

            assert len(candidates) == 1

            out_values.append((candidates[0], type_under_test))

        return out_values

    @pytest.fixture(name="value_type", params=["as_value", "as_generator"])
    def generator_or_no(self, request, type_under_test: type) -> type | None:
        return type_under_test if request.param == "as_generator" else None

    @pytest.fixture(name="value")
    def lazy_value(self, non_lazy_value, request: pytest.FixtureRequest, template_context):
        value_type = None  # DTFIX-FUTURE: get from request when needed, can't easily add to the static fixture list- the generator cases are not being tested
        if value_type:
            if isinstance(non_lazy_value, c.Mapping):
                generator = ((k, v) for k, v in non_lazy_value.items())
            else:
                generator = (item for item in non_lazy_value)

            value = generator

        else:
            value = _AnsibleLazyTemplateMixin._try_create(non_lazy_value)

        # any tests not marked `pytest.mark.allow_delazify` will supply a lazy with its _templar removed and assert that it's still empty afterward
        allow_delazify = any(request.node.iter_markers('allow_delazify'))

        if isinstance(value, _AnsibleLazyTemplateMixin) and not allow_delazify:
            assert value._templar
            # supply a non-functional, but non-None templar, forcing an error if lazy behavior is triggered during tagging
            value._templar = object()  # type: ignore[assignment]

        yield value  # yield to the test; we'll validate later

        # LazyAccessTuple can't template, so we can't induce this failure
        if isinstance(value, _AnsibleLazyTemplateMixin) and not allow_delazify and not isinstance(value, _AnsibleLazyAccessTuple):
            with pytest.raises(AttributeError):
                # verify using the templar fails by using a method which relies on it (to ensure our templar hack above worked)
                t.cast(AnsibleTaggedObject, value)._native_copy()
