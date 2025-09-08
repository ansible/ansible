# DTFIX5: more thorough tests are needed here, this is just a starting point

from __future__ import annotations

import collections.abc as c
import copy
import re
import sys
import typing as t

import pytest

from ansible.errors import AnsibleTemplateError, AnsibleUndefinedVariable
from ansible._internal._templating._jinja_bits import is_possibly_template
from ansible._internal._templating._jinja_common import CapturedExceptionMarker, MarkerError, JinjaCallContext, Marker
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible._internal._templating._utils import TemplateContext, LazyOptions
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateMixin, _AnsibleLazyTemplateList, _AnsibleLazyTemplateDict, _LazyValue, \
    _AnsibleLazyAccessTuple, UnsupportedConstructionMethodError
from ansible.module_utils._internal._datatag import AnsibleTaggedObject

from ...module_utils.datatag.test_datatag import ExampleSingletonTag
from ...test_utils.controller.display import emits_warnings

TRUST = TrustedAsTemplate()

VALUE_TO_TEMPLATE = TRUST.tag("{{ 'hello' | default('goodbye') }}")

CONTAINER_VALUES = (
    dict(hello=VALUE_TO_TEMPLATE),
    [VALUE_TO_TEMPLATE],
)


@pytest.mark.parametrize("value", CONTAINER_VALUES, ids=[type(value).__name__ for value in CONTAINER_VALUES])
def test_container_equality(value: t.Any) -> None:
    templar = TemplateEngine()

    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        # NOTE: Assertion failure helper text may be misleading, since repr() will show rendered templates, which will appear to match expected values.

        lazy = _AnsibleLazyTemplateMixin._try_create(value)

        assert lazy == lazy  # pylint: disable=comparison-with-itself

        assert lazy == rendered
        assert rendered == lazy

        assert lazy != value
        assert value != lazy


@pytest.mark.parametrize("value", CONTAINER_VALUES, ids=[type(value).__name__ for value in CONTAINER_VALUES])
def test_container_format(value: t.Any) -> None:
    templar = TemplateEngine()

    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        # NOTE: Assertion failure helper text may be misleading, since repr() will show rendered templates, which will appear to match expected values.

        lazy = _AnsibleLazyTemplateMixin._try_create(value)

        assert "{0}".format(lazy) == "{0}".format(rendered)


@pytest.mark.parametrize("container_type", (
    list,
))
def test_container_contains(container_type: type) -> None:
    templar = TemplateEngine()

    # including default('goodbye') as canary for flattening to a string
    value = container_type([VALUE_TO_TEMPLATE])
    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        # NOTE: Assertion failure helper text may be misleading, since repr() will show rendered templates, which will appear to match expected values.

        lazy = _AnsibleLazyTemplateMixin._try_create(value)

        for src in (lazy, rendered):
            assert 'hello' in src
            assert 'goodbye' not in src


@pytest.mark.parametrize("container_type", (
    list,
    # no need to test a tuple, it's just converted to a list
))
def test_container_comparison(container_type: type) -> None:
    templar = TemplateEngine()

    # including default('goodbye') as canary for flattening to a string
    value = container_type([VALUE_TO_TEMPLATE])
    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        # NOTE: Assertion failure helper text may be misleading, since repr() will show rendered templates, which will appear to match expected values.

        lazy = _AnsibleLazyTemplateMixin._try_create(value)

        assert value > rendered
        assert not (lazy > rendered)  # pylint: disable=unnecessary-negation

        assert value >= rendered
        assert lazy >= rendered

        assert rendered < value
        assert not (rendered < lazy)  # pylint: disable=unnecessary-negation

        assert rendered <= value
        assert rendered <= lazy


def test_list_sort() -> None:
    templar = TemplateEngine()

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        lazy: list = _AnsibleLazyTemplateMixin._try_create([TRUST.tag('{{ 2 }}'), TRUST.tag('{{ 1 }}')])
        lazy.sort()

        assert lazy == [1, 2]


def test_list_index() -> None:
    templar = TemplateEngine()

    rendered = templar.template(VALUE_TO_TEMPLATE)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        lazy: list = _AnsibleLazyTemplateMixin._try_create([VALUE_TO_TEMPLATE])

        assert lazy.index(rendered) == 0


def test_list_remove() -> None:
    templar = TemplateEngine()

    rendered = templar.template(VALUE_TO_TEMPLATE)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        lazy: list = _AnsibleLazyTemplateMixin._try_create([VALUE_TO_TEMPLATE])

        assert rendered in lazy

        lazy.remove(rendered)

        assert lazy == []


def test_dict_get_with_default(template_context) -> None:
    """Ensure getting a default value does not result in templating or storage of the default."""
    my_dict = _AnsibleLazyTemplateMixin._try_create({})
    value = TrustedAsTemplate().tag("{{ 1 }}")

    my_dict['x'] = TrustedAsTemplate().tag("{{ 2 }}")

    result = my_dict.get('a', value)

    assert result is value
    assert 'a' not in my_dict


def test_dict_setdefault(template_context) -> None:
    """Ensure that setdefault templates existing values, but not defaults."""
    my_dict = _AnsibleLazyTemplateMixin._try_create(dict(invalid_template=TRUST.tag("{{ 1/0 }}"), valid_template=TRUST.tag("{{ 1 }}")))
    value_for_default = TrustedAsTemplate().tag("{{ 'default' }}")

    assert my_dict.setdefault('valid_template') == 1
    assert my_dict.setdefault('valid_template', value_for_default) == 1
    assert my_dict.setdefault('nonexistent_key', value_for_default) is value_for_default

    result = my_dict.setdefault('invalid_template', value_for_default)
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)

    # repeat to ensure we didn't record any change
    result = my_dict.setdefault('invalid_template', value_for_default)
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)


def test_dict_pop(template_context) -> None:
    """Ensure that pop does not template or store its default, and that templating occurs before the collection is mutated."""
    my_dict = _AnsibleLazyTemplateMixin._try_create(dict(busted_template=TRUST.tag("{{ 1 / 0 }}")))
    value_for_default = TRUST.tag("{{ 1 }}")

    result = my_dict.pop("boguskey", value_for_default)

    assert result is value_for_default
    assert "boguskey" not in my_dict

    with JinjaCallContext(accept_lazy_markers=False):
        with pytest.raises(MarkerError):
            my_dict.pop('busted_template')

    assert 'busted_template' in my_dict

    result = my_dict.pop('busted_template')

    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)

    assert 'busted_template' not in my_dict


def test_dict_popitem(template_context):
    """Ensure popitem respects insertion order, templating of values, and that templating occurs before the collection is mutated."""
    my_dict = _AnsibleLazyTemplateMixin._try_create(dict(
        also_valid_template=TRUST.tag("{{ 0 }}"),
        busted_template=TRUST.tag("{{ 1 / 0 }}"),
        valid_template=TRUST.tag("{{ 1 }}"),
    ))

    assert my_dict.popitem() == ('valid_template', 1)

    with JinjaCallContext(accept_lazy_markers=False):
        with pytest.raises(MarkerError):
            my_dict.popitem()

    assert 'busted_template' in my_dict

    raw_result = my_dict.popitem()

    assert isinstance(raw_result, tuple)

    key, result = raw_result

    assert key == 'busted_template'
    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)

    assert my_dict.popitem() == ('also_valid_template', 0)

    with pytest.raises(KeyError):
        my_dict.popitem()


@pytest.mark.parametrize("native_value, expression", (
    ({}, 'obj.popitem()'),
    ([], 'obj.pop()'),
    ({}, 'obj.pop("missing")'),
    ([], 'obj.pop(1)'),
))
def test_get_errors(template_context, native_value: object, expression: str) -> None:
    """Verify getting a value from a lazy container fails the same as the native container when the requested key/index is missing or the container is empty."""
    lazy_value = _AnsibleLazyTemplateMixin._try_create(native_value)

    with pytest.raises(Exception) as native_error:
        eval(expression, dict(obj=native_value))

    with pytest.raises(type(native_error.value), match=f'^{re.escape(str(native_error.value))}$'):
        eval(expression, dict(obj=lazy_value))


def test_dict_items_and_values() -> None:
    templar = TemplateEngine()

    value = dict(key=VALUE_TO_TEMPLATE)
    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        lazy: dict = _AnsibleLazyTemplateMixin._try_create(value)

        assert list(lazy.items()) == list(rendered.items())
        assert list(lazy.values()) == list(rendered.values())


@pytest.mark.parametrize("template, variables, expected", [
    ("{{ (d1 | items) + (d2 | items) }}", dict(d1=dict(a=1), d2=dict(b=2)), [['a', 1], ['b', 2]]),
    ("{{ (d1 | items) + [('c', 3)] }}", dict(d1=dict(a=1)), [['a', 1], ['c', 3]]),
    ("{{ [('c', 3)] + (d1 | items) }}", dict(d1=dict(a=1)), [['c', 3], ['a', 1]]),
    ("{{ (d1 | items) * 2 }}", dict(d1=dict(a=1)), [['a', 1], ['a', 1]]),
    ("{{ 2 * (d1 | items) }}", dict(d1=dict(a=1)), [['a', 1], ['a', 1]]),
    ("{{ (1, 2) }}", dict(), [1, 2]),
])
def test_lazy_list_adapter_operators(template, variables, expected) -> None:
    templar = TemplateEngine(variables=variables)

    assert templar.template(TRUST.tag(template)) == expected


@pytest.mark.parametrize("expression, expected_value, expected_type", [
    ("l1 + l2", [_LazyValue(1), _LazyValue(2)], _AnsibleLazyTemplateList),  # __add__
    ("l1 + l2f()", [1, 2], list),  # __add__ (different lazy options)
    ("l1 + [2]", [_LazyValue(1), 2], _AnsibleLazyTemplateList),  # __add__
    ("[1] + l2", [1, _LazyValue(2)], _AnsibleLazyTemplateList),  # __radd__
    ("l1 * 3", [_LazyValue(1), _LazyValue(1), _LazyValue(1)], _AnsibleLazyTemplateList),  # __mul__
    ("3 * l2", [_LazyValue(2), _LazyValue(2), _LazyValue(2)], _AnsibleLazyTemplateList),  # __rmul__
    ("d1 | d2", dict(a=1, b=2, c=2), dict),  # __or__
    ("d1 | {'b': 2, 'c': 2}", dict(a=1, b=2, c=2), dict),  # __or__
    ("{'a': 1} | d2", dict(a=1, b=2, c=2), dict),  # __ror__
    ("d1 |= d2", dict(d1=dict(a=_LazyValue(1), b=2, c=2)), _AnsibleLazyTemplateDict),  # __ior__
    ("d1 |= {'b': 2, 'c': 2}", dict(d1=dict(a=_LazyValue(1), b=2, c=2)), _AnsibleLazyTemplateDict),  # __ior__
    ('d1.copy()', dict(a=_LazyValue(1), c=_LazyValue(1)), _AnsibleLazyTemplateDict),  # _AnsibleLazyTemplateDict.copy
    ('type(d1)(d1)', dict(a=_LazyValue(1), c=_LazyValue(1)), _AnsibleLazyTemplateDict),  # _AnsibleLazyTemplateDict.__init__ copy
    ('l1.copy()', [_LazyValue(1)], _AnsibleLazyTemplateList),  # _AnsibleLazyTemplateList.copy
    ('type(l1)(l1)', [_LazyValue(1)], _AnsibleLazyTemplateList),  # _AnsibleLazyTemplateList.__init__ copy
    ('type(t1)(t1)', (1,), _AnsibleLazyAccessTuple),
    ('copy.copy(l1)', [_LazyValue(1)], _AnsibleLazyTemplateList),
    ('copy.copy(d1)', dict(a=_LazyValue(1), c=_LazyValue(1)), _AnsibleLazyTemplateDict),
    ('copy.deepcopy(l1)', [_LazyValue(1)], _AnsibleLazyTemplateList),  # __AnsibleLazyTemplateList.__deepcopy__
    ('copy.deepcopy(d1)', dict(a=_LazyValue(1), c=_LazyValue(1)), _AnsibleLazyTemplateDict),  # __AnsibleLazyTemplateDict.__deepcopy__
    ('ExampleSingletonTag().tag(l1)', [_LazyValue(1)], _AnsibleLazyTemplateList),
    ('ExampleSingletonTag().tag(d1)', dict(a=_LazyValue(1), c=_LazyValue(1)), _AnsibleLazyTemplateDict),
    ('list(reversed(l1))', [1], list),  # _AnsibleLazyTemplateList.__reversed__
    ('list(reversed(d1))', ['c', 'a'], list),  # dict.__reversed__ - keys only
    ('l1[:]', [_LazyValue(1)], _AnsibleLazyTemplateList),  # __getitem__ (slice)
    ('t1[:]', (1,), _AnsibleLazyAccessTuple),  # __getitem__ (slice)
    ('d1["a"]', 1, int),  # __getitem__
    ('d1.get("a")', 1, int),  # get
    ('l1[0]', 1, int),  # __getitem__
    ('d1.pop("a")', 1, int),  # dict.pop (check returned value)
    ('d1.pop("a");', dict(d1=dict(c=_LazyValue(1))), _AnsibleLazyTemplateDict),  # dict.pop (check mutated source)
    ('list(d1.items())', [('a', 1), ('c', 1)], list),  # items
    ('d1.popitem()', ('c', 1), tuple),  # dict.popitem (check returned value)
    ('d1.popitem();', dict(d1=dict(a=_LazyValue(1))), _AnsibleLazyTemplateDict),  # dict.popitem (check mutated source)
    ('d1.clear(); d1["d"] = 4', dict(d1=dict(d=4)), _AnsibleLazyTemplateDict),  # dict.clear (clear + mutate)
    ('d1["d"] = 4; d1.clear()', dict(d1=dict()), _AnsibleLazyTemplateDict),  # dict.clear (mutate + clear)
    ('d1.update(d2);', dict(d1=dict(a=_LazyValue(1), b=2, c=2)), _AnsibleLazyTemplateDict),  # dict.update
    ('d1.setdefault("d", 4)', 4, int),  # dict.setdefault (return value check only)
    ('d1.setdefault("d", 4);', dict(d1=dict(a=_LazyValue(1), c=_LazyValue(1), d=4)), _AnsibleLazyTemplateDict),  # dict.setdefault
    ('l1.clear(); l1.append(4)', dict(l1=[4]), _AnsibleLazyTemplateList),  # list.clear (clear + mutate)
    ('l1.append(4); l1.clear()', dict(l1=[]), _AnsibleLazyTemplateList),  # list.clear (mutate + clear)
    ('l1.pop()', 1, int),  # list.pop (check returned value)
    ('l1.pop();', dict(l1=[]), _AnsibleLazyTemplateList),  # list.pop (check returned value)
    ('l1.insert(0, 4);', dict(l1=[4, _LazyValue(1)]), _AnsibleLazyTemplateList),  # list.insert (check mutated source)
    ('l1.extend(l2);', dict(l1=[_LazyValue(1), 2]), _AnsibleLazyTemplateList),  # list.extend (check mutated source)
    ('l1[0] = 2;', dict(l1=[2]), _AnsibleLazyTemplateList),  # list.__setitem__ (check mutated source)
    ('l1 > [1]', False, bool),  # __gt__ (lazy vs constant)
    ('l1 > l1x', False, bool),  # __gt__ (lazy vs lazy)
    ('l1 >= [1]', True, bool),  # __ge__ (lazy vs constant)
    ('l1 >= l1x', True, bool),  # __ge__ (lazy vs lazy)
    ('l1 < [1]', False, bool),  # __lt__ (lazy vs constant)
    ('l1 < l1x', False, bool),  # __lt__ (lazy vs lazy)
    ('l1 <= [1]', True, bool),  # __le__ (lazy vs constant)
    ('l1 <= l1x', True, bool),  # __le__ (lazy vs lazy)
    ('l1 == [1]', True, bool),  # __eq__ (lazy vs constant)
    ('l1 == l1x', True, bool),  # __eq__ (lazy vs lazy)
    ('l1 != [1]', False, bool),  # __ne__ (lazy vs constant)
    ('l1 != l1x', False, bool),  # __ne__ (lazy vs lazy)
    ('d1 == {"a": 1, "c": 1}', True, bool),  # __eq__ (lazy vs constant)
    ('d1 == d1x', True, bool),  # __eq__ (lazy vs lazy)
    ('d1 != {"a": 1, "c": 1}', False, bool),  # __ne__ (lazy vs constant)
    ('d1 != d1x', False, bool),  # __eq__ (lazy vs lazy)
    ('1 in l1', True, bool),  # __contains__
    ('str(d1)', str(dict(a=1, c=1)), str),  # __str__
    ('str(l1)', str([1]), str),  # __str__
    ('repr(d1)', repr(dict(a=1, c=1)), str),  # __repr__
    ('repr(l1)', repr([1]), str),  # __repr__
    ('"{}".format(l1)', repr([1]), str),  # __format__ [no override required]
    ('list(l1)', [1], list),  # _AnsibleLazyTemplateList.__iter__
    ('list(d1)', ['a', 'c'], list),  # _AnsibleLazyTemplateDict.__iter__
    ('l1._native_copy()', [1], list),  # native_copy
    ('dict(d1)', dict(a=1, c=1), dict),  # __iter__
    ('d1._native_copy()', dict(a=1, c=1), dict),  # native_copy
    ('{} + l1', "unsupported operand type(s) for +: 'dict' and '_AnsibleLazyTemplateList'", TypeError),  # __radd__
    ('d1 + l1', "unsupported operand type(s) for +: '_AnsibleLazyTemplateDict' and '_AnsibleLazyTemplateList'", TypeError),  # __radd__
    ('d1 + []', "unsupported operand type(s) for +: '_AnsibleLazyTemplateDict' and 'list'", TypeError),  # python operator dispatch
    ('set() + l1', "unsupported operand type(s) for +: 'set' and '_AnsibleLazyTemplateList'", TypeError),  # python operator dispatch
    ('set() + d1', "unsupported operand type(s) for +: 'set' and '_AnsibleLazyTemplateDict'", TypeError),  # python operator dispatch
    ('l1 + {}', 'can only concatenate list (not "dict") to list', TypeError),  # __add__ (relies on list.__add__)
    ('l1 + set()', 'can only concatenate list (not "set") to list', TypeError),  # __add__ (relies on list.__add__)
    ('l1 + tuple()', 'can only concatenate list (not "tuple") to list', TypeError),  # __add__ (relies on list.__add__)
    ('tuple() + l1', 'can only concatenate tuple (not "_AnsibleLazyTemplateList") to tuple', TypeError),  # __radd__ (relies on tuple.__add__)
    ('tuple() + d1', 'can only concatenate tuple (not "_AnsibleLazyTemplateDict") to tuple', TypeError),  # relies on tuple.__add__
    ('l1.pop(42)', "pop index out of range", IndexError),
    ('type(l1)([])', 'Direct construction of lazy containers is not supported.', UnsupportedConstructionMethodError),
    ('type(t1)([])', 'Direct construction of lazy containers is not supported.', UnsupportedConstructionMethodError),
    ('type(d1)({})', 'Direct construction of lazy containers is not supported.', UnsupportedConstructionMethodError),
], ids=str)
def test_lazy_container_operators(expression: str, expected_value: t.Any, expected_type: type) -> None:
    """
    Verify that lazy container operators and methods properly implement lazy behavior.
    Results are checked both for expected types and expected values.
    When the result is a container, items in the container are checked to see if they're lazy as appropriate.
    This test uses a function to simulate Jinja plugin behavior, since plugins can use operators and methods that Jinja expressions cannot.
    """
    # DTFIX5: add a unit test to ensure every list/dict method has been overridden or on a list we can safely ignore
    def l2f() -> list:
        """Return a lazy list that uses different lazy options, to ensure it cannot be lazy combined."""
        return TemplateContext.current().templar.template([2], lazy_options=LazyOptions.SKIP_TEMPLATES)

    variables = dict(
        one=1,
        two=2,
        data=dict(
            l1=[TRUST.tag('{{ one }}')],
            l1x=[TRUST.tag('{{ one }}')],
            l2=[TRUST.tag('{{ two }}')],
            l2f=l2f,
            t1=(TRUST.tag('{{ one }}'),),
            d1=dict(a=TRUST.tag('{{ one }}'), c=TRUST.tag('{{ one }}')),
            d1x=dict(a=TRUST.tag('{{ one }}'), c=TRUST.tag('{{ one }}')),
            d2=dict(b=TRUST.tag('{{ two }}'), c=TRUST.tag('{{ two }}')),
        ),
    )

    def run_test(data: dict[str, t.Any]) -> t.Any:
        nonlocal expected_value

        secondary_templar = TemplateEngine()

        # Run under a secondary context using a templar with no variables; this allows us to test the correct propagation and use of the
        # embedded templar in lazy containers. Templated values will not render correctly if they pick up the ambient (no-vars) templar during
        # various copy/operator scenarios.
        with TemplateContext(template_value='', templar=secondary_templar, options=TemplateOptions.DEFAULT, stop_on_template=False):
            code_globals = dict(
                copy=copy,
                ExampleSingletonTag=ExampleSingletonTag,
            )

            try:
                result = eval(expression, code_globals, data)
            except SyntaxError:
                # some expressions use a semicolon to force exec instead of eval, even if they only need a single statement
                exec(expression, code_globals, data)

                var_name = list(expected_value)[0]
                expected_value = expected_value[var_name]
                result = data[var_name]
            except Exception as ex:
                if type(ex) is not expected_type:  # pylint: disable=unidiomatic-typecheck
                    # we weren't expecting an exception, or got one of the wrong type; re-raise it now for the traceback instead of just a failed assertion
                    raise

                result = ex

        assert type(result) is expected_type  # pylint: disable=unidiomatic-typecheck

        expected_result: t.Any  # avoid type narrowing

        if issubclass(expected_type, list):
            assert isinstance(result, list)  # redundant, but assists mypy in understanding the type

            expected_list_types = [type(value) for value in expected_value]
            expected_result = [value.value if isinstance(value, _LazyValue) else value for value in expected_value]

            actual_list_types: list[type] = [type(value) for value in list.__iter__(result)]

            assert actual_list_types == expected_list_types
        elif issubclass(expected_type, tuple):
            assert isinstance(result, tuple)  # redundant, but assists mypy in understanding the type

            expected_tuple_types = [type(value) for value in expected_value]
            expected_result = expected_value

            actual_tuple_types: list[type] = [type(value) for value in tuple.__iter__(result)]

            assert actual_tuple_types == expected_tuple_types
        elif issubclass(expected_type, dict):
            assert isinstance(result, dict)  # redundant, but assists mypy in understanding the type

            expected_dict_types = {key: type(value) for key, value in expected_value.items()}
            expected_result = {key: value.value if isinstance(value, _LazyValue) else value for key, value in expected_value.items()}

            actual_dict_types: dict[str, type] = {key: type(value) for key, value in dict.items(result)}

            assert actual_dict_types == expected_dict_types
        elif issubclass(expected_type, Exception):
            result = str(result)  # unfortunately exceptions can't be compared for equality, so use the string representation instead
            expected_result = expected_value
        else:
            expected_result = expected_value

        assert result == expected_result

    templar = TemplateEngine(variables=variables)
    templar.environment.globals['run_test'] = run_test
    templar.template(TRUST.tag('{{ run_test(data=data) }}'))


def test_range_templating():
    """
    Verify special handling for Range objects.
    They are usually listified like other iterables when returned from a Jinja filter or method/function call, except when calling the Python `range()`
    global function directly, which allows the range object to be returned and used directly.
    """
    templar = TemplateEngine(variables=dict(
        large_value=min(1000000000000, sys.maxsize - 1)  # ensure we don't exceed ssize_t on 32-bit systems
    ))

    # ensure that an insanely large range is not listified
    assert templar.evaluate_conditional(TRUST.tag("range(large_value) | type_debug == 'range'"))
    assert isinstance(templar.template(TRUST.tag("{{ range(large_value) | random }}")), int)
    assert templar.template(TRUST.tag("{{ range(3) | reverse }}")) == [2, 1, 0]


@pytest.mark.parametrize("value", [
    "{{ range(10000) }}",
    "{{ [range(10000)] }}",
    "{{ {'a': range(10000)} }}",
])
def test_range_template_fail(value):
    """Verify unsupported range object usages."""
    with pytest.raises(AnsibleTemplateError):
        TemplateEngine().template(TRUST.tag(value))


LISTIFIED_ITERATOR_VALUES_AND_EXPECTED = (
    ("{'a': 1, 'b': 2}.items()", [('a', 1), ('b', 2)]),
    ("['hi'] | map('upper')", ["HI"]),
)

LISTIFIED_ITERATOR_VALUES = tuple(item[0] for item in LISTIFIED_ITERATOR_VALUES_AND_EXPECTED)
LISTIFIED_ITERATOR_TEMPLATES = tuple(TRUST.tag(f'{{{{ {value} }}}}') for value in LISTIFIED_ITERATOR_VALUES)


@pytest.mark.parametrize("value, expected", LISTIFIED_ITERATOR_VALUES_AND_EXPECTED)
def test_list_adapter_equality(value: str, expected: list) -> None:
    origin = Origin(path='/test')  # here to make sure it doesn't trigger an exception, it won't be in the result

    assert TemplateEngine().evaluate_expression(TRUST.tag(origin.tag(f"{value} == {expected}")))


@pytest.mark.parametrize("value", LISTIFIED_ITERATOR_VALUES)
def test_list_adapter_source_propagation(value: t.Any) -> None:
    origin = Origin(path='/test')

    assert Origin.get_tag(TemplateEngine().template(TRUST.tag(origin.tag(f"{{{{ {value} }}}}")))) is origin


@pytest.mark.parametrize("value", t.cast(tuple, CONTAINER_VALUES) + LISTIFIED_ITERATOR_TEMPLATES, ids=str)
def test_lazy_containers_to_yaml(value: t.Any) -> None:
    TemplateEngine(variables=dict(value=value)).template(TRUST.tag("{{ value | to_yaml }}"))


@pytest.mark.parametrize("value", t.cast(tuple, CONTAINER_VALUES) + LISTIFIED_ITERATOR_TEMPLATES, ids=str)
def test_lazy_containers_to_json(value: t.Any) -> None:
    TemplateEngine(variables=dict(value=value)).template(TRUST.tag("{{ value | to_json }}"))


@pytest.mark.parametrize("value", (_AnsibleLazyTemplateDict, _AnsibleLazyTemplateList))
def test_lazy_interface(value: type[_AnsibleLazyTemplateMixin]) -> None:
    """Ensure that lazy containers implement all the methods that their native types provide."""
    missing = set(dir(value._native_type)) - set(dir(value))
    assert not missing


@pytest.mark.parametrize("expression, expected", (
    ("l1[0]", [0]),  # _AnsibleLazyTemplateList.__getitem__ and _ansible_finalize (list to lazy list)
    ("l1[1]", [1]),  # _AnsibleLazyTemplateList.__getitem__
    ("l1[2]", 'hello'),  # _AnsibleLazyTemplateList.__getitem__
    ("[v for v in l1][0]", [0]),  # _AnsibleLazyTemplateList.__iter__ and _ansible_finalize (list to lazy list)
    ("[v for v in l1][1]", [1]),  # _AnsibleLazyTemplateList.__iter__
    ("[v for v in l1][2]", 'hello'),  # _AnsibleLazyTemplateList.__iter__
    ("d1['a']", [0]),  # _AnsibleLazyTemplateDict.__getitem__ and _ansible_finalize (dict to lazy dict)
    ("d1['b']", [1]),  # _AnsibleLazyTemplateDict.__getitem__
    ("d1['c']", 'hello'),  # _AnsibleLazyTemplateDict.__getitem__
    ("{k: v for k, v in d1.items()}['a']", [0]),  # _AnsibleLazyTemplateDict.items and _ansible_finalize (dict to lazy dict)
    ("{k: v for k, v in d1.items()}['b']", [1]),  # _AnsibleLazyTemplateDict.items
    ("{k: v for k, v in d1.items()}['c']", 'hello'),  # _AnsibleLazyTemplateDict.items
), ids=str)
def test_lazy_persistence(expression: str, expected: t.Any) -> None:
    """
    Verify that values returned from lazy containers are persistent, regardless of whether templating is involved or not.
    A global function is used to simulate the behavior that would occur in a Jinja plugin.
    """
    variables = dict(
        data=dict(
            l1=[TRUST.tag('{{ [0] }}'), [1], 'hello'],
            d1=dict(a=TRUST.tag('{{ [0] }}'), b=[1], c='hello'),
        ),
    )

    def run_test(data: dict[str, t.Any]) -> None:
        first = eval(expression, data)
        second = eval(expression, data)

        assert first == expected
        assert first is second

    templar = TemplateEngine(variables=variables)
    templar.environment.globals['run_test'] = run_test

    templar.template(TRUST.tag("{{ run_test(data=data) }}"))


@pytest.mark.parametrize("expression", (
    "data['l1'][0]",
    "data['d1']['a']",
))
def test_lazy_mutation_persistence(expression: str) -> None:
    """Verify that lazy containers persist values added after creation and return them as-is without modification, even if they contain trusted templates."""
    # DTFIX5: investigate relevance of this test now that mutation/dirty tracking is toast
    variables = dict(
        data=dict(
            l1=[None],
            d1=dict(a=None),
        ),
    )

    def run_test(data: dict[str, t.Any]) -> None:
        assert data

        value = [TRUST.tag('{{ "hi" }}')]

        exec(f'{expression} = value')

        result = eval(expression)

        assert result is value

    templar = TemplateEngine(variables=variables)
    templar.environment.globals['run_test'] = run_test

    templar.template(TRUST.tag("{{ run_test(data=data) }}"))


@pytest.mark.parametrize("expr, new_value, some_var, expected_value", [
    ("access_and_mutate_dict(mutate_dict(some_var))", TRUST.tag("{{ 'mom' }}"), dict(one="one"), dict(one="one", new="{{ 'mom' }}", secondnew="{{ 'mom' }}")),
    ("access_and_mutate_list(mutate_list(some_var))", TRUST.tag("{{ 'mom' }}"), ["one"], ["one", "{{ 'mom' }}", "{{ 'mom' }}"]),
])
def test_lazy_mutation_cross_plugin_dirty_container(expr: str, new_value: t.Any, some_var: t.Any, expected_value: t.Any):
    """Ensure that new templates sourced from a plugin are not processed by subsequent plugins or template finalization."""
    # DTFIX5: investigate relevance of this test now that mutation/dirty tracking is toast
    def mutate_list(value: list) -> list:
        value.append(new_value)

        assert value[1] is new_value

        return value

    def access_and_mutate_list(value: list) -> list:
        value.append(new_value)

        assert value[2] is new_value
        assert value[1] == expected_value[1]

        return value

    def mutate_dict(value: dict) -> dict:
        value['new'] = new_value

        assert value['new'] is new_value

        return value

    def access_and_mutate_dict(value: t.Any) -> list:
        value['secondnew'] = new_value

        assert value['secondnew'] is new_value
        assert value['new'] == expected_value['new']

        return value

    available_vars = dict(some_var=some_var,
                          access_and_mutate_list=access_and_mutate_list,
                          mutate_list=mutate_list,
                          access_and_mutate_dict=access_and_mutate_dict,
                          mutate_dict=mutate_dict)

    res = TemplateEngine(variables=available_vars).evaluate_expression(TRUST.tag(expr))
    assert res == expected_value


def test_undefined_in_jinja_constant_container():
    """
    Retrieval of an undefined value in a plugin which does not declare undefined support should internally raise AnsibleUndefinedVariable, which, if
    unhandled by the plugin, will be converted to an AnsibleUndefined and returned as the result of that plugin's invocation, allowing the template
    to continue execution.
    """

    plugin_retrieved_the_value = False

    def demo(_input, arg):
        nonlocal plugin_retrieved_the_value
        _x = arg[0]
        plugin_retrieved_the_value = True
        return []

    templar = TemplateEngine()
    templar.environment.filters['demo'] = demo

    with pytest.raises(AnsibleUndefinedVariable):
        x = templar.template(TRUST.tag("{{ True | demo([bogus_var]) }}"))
        pass
    assert not plugin_retrieved_the_value

    assert templar.template(TRUST.tag("{{ True | demo([bogus_var]) | default('nope') }}")) == 'nope'
    assert not plugin_retrieved_the_value


class CustomSequence(c.Sequence):
    def __init__(self, values) -> None:
        self._content = list(values)

    def __getitem__(self, item) -> t.Any:
        return self._content[item]

    def __len__(self) -> int:
        return len(self._content)


@pytest.mark.parametrize("expression, expected_result", (
    # verify templates sourced by plugins are not auto-templated
    ("list_with_bad_template() | pass_through is first_item_unrendered", True),  # plain list return values are lazy wrapped, but not templated
    ("tuple_with_bad_template() | pass_through is first_item_unrendered", True),  # tuples are not lazified, but suppressed unsupported type warning
    # verify markers are tripped on managed access, but not unmanaged access (they will still trip on use, which is not tested here)
    ("list_with_undefined() | pass_through is first_item_trips", True),  # managed access trips
    ("tuple_with_undefined() | pass_through is first_item_trips", True),  # managed access trips
    ("custom_sequence_with_undefined() | pass_through is first_item_trips", False),  # unmanaged access doesn't trip
    # verify that Jinja constant containers are wrapped where possible
    ("['{{ 1 }}'] | pass_through is first_item_unrendered", True),
    ("[bogusvar] | pass_through is first_item_trips", True),
    ("{'k': bogusvar} | pass_through is first_item_trips", True),
    ("(bogusvar,) | pass_through is first_item_trips", True),
    # verify that plugins directly invoking tests and filters do not trigger auto-templating
    ('call_filter_with_native_args_kwargs()', True),  # `call_filter` invocations with plain list/dict should be lazy non-templating
    ('call_test_with_native_args_kwargs()', True),  # `call_test` invocations with plain list/dict should be lazy non-templating
))
def test_plugin_result_wrapping(expression: str, expected_result: t.Any, _ignore_untrusted_template) -> None:
    """
    Validate various intra-plugin container behaviors:
     * A plain list/dict returned by a Jinja call/plugin gets lazified, but with templating disabled (feature parity with pre-2.19).
     * Tuple/set returned by a Jinja call/plugin receives no special behavior.
     * Jinja plugins that do not accept markers should raise when accessing one from a lazy container.
    The default test "untrusted template as error" behavior is disabled, since some test cases involve accessing untrusted templates.
    """
    templar = TemplateEngine()

    def list_with_bad_template() -> list[str]:
        return [TRUST.tag('{{ 1 / 0 }}')]

    def list_with_undefined() -> list[Marker]:
        return [TemplateEngine().template(TRUST.tag('{{ bogusvar }}'))]

    def tuple_with_bad_template() -> tuple[str, ...]:
        return (TRUST.tag('{{ 1 / 0 }}'),)

    def tuple_with_undefined() -> tuple[Marker, ...]:
        return (TemplateEngine().template(TRUST.tag('{{ bogusvar }}')),)

    def custom_sequence_with_undefined() -> CustomSequence:
        return CustomSequence((TemplateEngine().template(TRUST.tag('{{ bogusvar }}')),))

    def pass_through(value: t.Any) -> t.Any:
        return value

    def first_item_trips(value: c.Sequence | c.Mapping) -> bool:
        if isinstance(value, c.Mapping):
            key_or_idx = list(value.keys())[0]
        else:
            key_or_idx = 0

        try:
            value[key_or_idx]
        except MarkerError:
            return True

        return False

    def first_item_unrendered(value: c.Sequence) -> bool:
        return isinstance(value[0], str) and is_possibly_template(value[0])

    def call_filter_with_native_args_kwargs() -> t.Any:
        return templar.environment.call_filter('args_and_kwargs_are_non_templating_lazy', value=42, args=[[1]], kwargs=dict(kwarg=[2]))

    def call_test_with_native_args_kwargs() -> t.Any:
        return templar.environment.call_test('args_and_kwargs_are_non_templating_lazy', value=42, args=[[1]], kwargs=dict(kwarg=[2]))

    def args_and_kwargs_are_non_templating_lazy(value: t.Any, arg, *, kwarg) -> bool:
        return (
            value == 42 and
            isinstance(arg, _AnsibleLazyTemplateList) and
            not arg._lazy_options.template and
            isinstance(kwarg, _AnsibleLazyTemplateList) and
            not kwarg._lazy_options.template
        )

    templar.environment.globals.update(
        list_with_bad_template=list_with_bad_template,
        list_with_undefined=list_with_undefined,
        tuple_with_bad_template=tuple_with_bad_template,
        tuple_with_undefined=tuple_with_undefined,
        custom_sequence_with_undefined=custom_sequence_with_undefined,
        call_filter_with_native_args_kwargs=call_filter_with_native_args_kwargs,
        call_test_with_native_args_kwargs=call_test_with_native_args_kwargs,
    )

    templar.environment.filters.update(
        pass_through=pass_through,
        args_and_kwargs_are_non_templating_lazy=args_and_kwargs_are_non_templating_lazy,
    )

    templar.environment.tests.update(
        first_item_unrendered=first_item_unrendered,
        first_item_trips=first_item_trips,
        args_and_kwargs_are_non_templating_lazy=args_and_kwargs_are_non_templating_lazy,
    )

    expression = TRUST.tag(expression)

    with emits_warnings(warning_pattern=[], deprecation_pattern=[]):
        result = templar.evaluate_expression(expression)

    assert result == expected_result


def test_lazy_options_propagation(template_context):
    """Ensure that lazy collections propagate lazy options to child lazies."""
    src_template = "{{ 1 / 0 }}"

    def nested_container_with_template() -> t.Any:
        return [[TRUST.tag(src_template)]]

    templar = TemplateEngine()
    templar.environment.globals.update(nested_container_with_template=nested_container_with_template)

    res = templar.template(TRUST.tag('{{ nested_container_with_template() }}'))

    assert isinstance(res, _AnsibleLazyTemplateList)
    assert not res._lazy_options.template  # ensure call output skips templating
    assert isinstance(res[0], _AnsibleLazyTemplateList)
    assert res[0]._lazy_options is res._lazy_options  # ensure the parent options are propagated
    assert res[0][0] == src_template


def test_subclass_dispatch_collision():
    """Simulate a developer error by creating a new lazy container subclass with colliding base and/or tagged type dispatch entries."""

    class _TestBaseType: ...
    class _TaggedTestBaseType(_TestBaseType, AnsibleTaggedObject): ...
    class _LazyTaggedTestBaseType(_TaggedTestBaseType, _AnsibleLazyTemplateMixin): ...

    with pytest.raises(
        TypeError,
        match=f"Lazy mixin '_OopsConflictingLazyTaggedTestBaseType' type '_TaggedTestBaseType' conflicts with {_LazyTaggedTestBaseType.__name__!r}.",
    ):
        class _OopsConflictingLazyTaggedTestBaseType(_TaggedTestBaseType, _AnsibleLazyTemplateMixin): ...
        assert _OopsConflictingLazyTaggedTestBaseType  # pragma: nocover

    with pytest.raises(
        TypeError,
        match=f"Lazy mixin '_OopsConflictingTestBaseType' type '_TestBaseType' conflicts with {_LazyTaggedTestBaseType.__name__!r}.",
    ):
        class _OopsConflictingTestBaseType(_TestBaseType, _AnsibleLazyTemplateMixin): ...
        assert _OopsConflictingTestBaseType  # pragma: nocover


_L = ['a']
_D = dict(B='b')
_T = ('c',)


@pytest.mark.parametrize("value, deep", (
    ([_L, _D, _T], False),
    ([_L, _D, _T], True),
    (dict(L=_L, D=_D, T=_T), False),
    (dict(L=_L, D=_D, T=_T), True),
    ((_L, _D, _T), False),
    ((_L, _D, _T), True),
), ids=str)
def test_lazy_copies(value: list | dict, deep: bool, template_context: TemplateContext) -> None:
    """Verify that `copy.copy` and `copy.deepcopy` make lazy copies of lazy containers."""
    # pylint: disable=unnecessary-dunder-call
    original = _AnsibleLazyTemplateMixin._try_create(value)
    base_type = type(value)
    pseudo_lazy = base_type is tuple  # tuples do not wrap their values in `_LazyValue`

    keys: list

    if base_type is list or base_type is tuple:
        keys = list(range(len(original)))
    else:
        keys = list(original)

    assert all(isinstance(base_type.__getitem__(original, key), _LazyValue) != pseudo_lazy for key in keys)  # lazy before copy

    if deep:
        copied = copy.deepcopy(original)
    else:
        copied = copy.copy(original)

    assert copied is not original
    assert len(copied) == len(original)
    assert pseudo_lazy or all(isinstance(base_type.__getitem__(original, key), _LazyValue) != pseudo_lazy for key in keys)  # still lazy after copy

    assert all((base_type.__getitem__(copied, key) is base_type.__getitem__(original, key)) != deep for key in keys)
    assert (copied._templar is original._templar) != deep
    assert (copied._lazy_options is original._lazy_options) != deep


def test_lazy_template_mixin_init() -> None:
    """
    Verify `_AnsibleLazyTemplateMixin` checks the __init__ arg type.
    This code path is not normally reachable, since types which use it perform the same check before invoking the mixin.
    """
    with pytest.raises(UnsupportedConstructionMethodError):
        _AnsibleLazyTemplateMixin(t.cast(t.Any, None))
