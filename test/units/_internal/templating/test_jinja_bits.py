from __future__ import annotations

import pathlib
import sys
import typing as t

from contextlib import nullcontext

import pytest
import pytest_mock

from ansible._internal import _display_utils
from ansible._internal._templating._access import NotifiableAccessContextBase
from ansible.errors import AnsibleUndefinedVariable, AnsibleTemplateError
from ansible._internal._templating._errors import AnsibleTemplatePluginRuntimeError
from ansible.module_utils._internal._datatag import AnsibleTaggedObject
from ansible._internal._templating._jinja_common import CapturedExceptionMarker, MarkerError, Marker, UndefinedMarker
from ansible._internal._templating._utils import TemplateContext
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible._internal._templating._jinja_bits import (AnsibleEnvironment, TemplateOverrides, _TEMPLATE_OVERRIDE_FIELD_NAMES, defer_template_error,
                                                       AnsibleTemplate, _BUILTIN_TEST_ALIASES)
from ansible._internal._templating import _jinja_plugins
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from jinja2.loaders import DictLoader

if t.TYPE_CHECKING:
    import unittest.mock

TRUST = TrustedAsTemplate()


@pytest.mark.parametrize("template,expected,variables,sources,options", [
    # no change; non-template data should be ignored
    (r'c:\newdir', r'c:\newdir', None, None, None),
    # default behavior always escapes backslashes in string constants in template expressions
    (r'{{ "c:\newdir" }}', r'c:\newdir', None, None, None),
    # escaping applies only to string literals in expressions in the current template; includes are never escaped
    (r'{{ "c:\newdir" }} {% include "foo" %}', r'c:\newdir c:\newdir', None,
     dict(foo=TRUST.tag(r'{{ "c:\\newdir" }}')), None),
    # escaping applies only to string literals in expressions in the current template; imports are never escaped
    (r'{{ "c:\newdir" }} {% import "foo" as foo %}{{ foo.m() }}', r'c:\newdir c:\newdir', None,
     dict(foo=TRUST.tag(r'{% macro m() %}{{ "c:\\newdir" }}{% endmacro %}')), None),
    # escape disable only applies to the current template; includes are still never escaped
    (r'{{ "c:\\newdir" }} {% include "foo" %}', r'c:\newdir c:\newdir', None,
     dict(foo=TRUST.tag(r'{{ "c:\\newdir" }}')), TemplateOptions(escape_backslashes=False)),
    # escape disable only applies to the current template; imports are still never escaped
    (r'{{ "c:\\newdir" }} {% import "foo" as foo %}{{ foo.m() }}', r'c:\newdir c:\newdir', None,
     dict(foo=TRUST.tag(r'{% macro m() %}{{ "c:\\newdir" }}{% endmacro %}')), TemplateOptions(escape_backslashes=False)),
    # escaping behavior should not apply to string constants in non-expression blocks (eg, `set`)
    (r'{% set foo="c:\\newdir" %}{{ foo }}', r'c:\newdir', None, None, None),
    # default behavior escapes indirect templates
    (r'{{ indirect }}', r'c:\newdir', dict(indirect=TRUST.tag(r'{{ "c:\newdir" }}')), None, None),
    # disable does *not* propagate to indirect template rendering
    (r'{{ "c:\\newdir" }} {{ indirect }}', r'c:\newdir c:\newdir',
     dict(indirect=TRUST.tag(r'{{ "c:\newdir" }}')), None, TemplateOptions(escape_backslashes=False)),
    # default escaping works on input containers
    (dict(key=TRUST.tag(r'{{ "c:\newdir" }}')), dict(key=r'c:\newdir'), None, None, None),
    # disable only applies to string templar inputs; templates in containers are always escaped
    (dict(key=TRUST.tag(r'{{ "c:\newdir" }}')), dict(key=r'c:\newdir'), None, None, TemplateOptions(escape_backslashes=False)),

])
def test_escape_backslashes(template: t.Any, expected: t.Any, variables: dict[str, t.Any], sources: dict[str, str], options: TemplateOptions | None) -> None:
    template = TRUST.tag(template)

    templar = TemplateEngine(loader=None, variables=variables)
    templar.environment.loader = DictLoader(sources or {})

    if options is None:
        options = TemplateOptions.DEFAULT

    assert templar.template(template, options=options) == expected


def test_templatemodule_ignore(template_context):
    """Ensure that `TemplateModule` silently passes through try_create()."""
    template = TRUST.tag('{% import "foo" as foo %}{{ foo }}')

    templar = TemplateEngine()
    templar.environment.loader = DictLoader(dict(foo=TRUST.tag('{{ undefined_in_import }}')))

    with _display_utils.DeferredWarningContext(variables=templar.available_variables) as warnings:
        result = templar.template(template)

    assert not warnings.get_warnings()
    assert isinstance(result, UndefinedMarker)


@pytest.mark.xfail(reason="template local propagation to nested templar calls is not implemented")
def test_context_local_propagation():
    trusted = TrustedAsTemplate()
    trusted_scalar = trusted.tag("{{ hi_from }}")
    play_vars = dict(
        hi_from="play var",
        templated_scalar=trusted_scalar,
        templated_dict=dict(
            templated_scalar=trusted_scalar,
        ),
    )
    templar = TemplateEngine(loader=None, variables=play_vars)

    # shared template fragment that we'll use both directly and in an imported template
    validate_me = "[hi_from, templated_scalar, templated_dict.templated_scalar, templated_dict]"

    # Imports are one of the rare cases where Jinja calls (Ansible)Template.new_context() itself and directly consumes/concats the results; need to ensure
    # that whatever solution gets implemented can handle that case as well (since it's easier to handle the cases where we own the new_context call).
    templar.environment.loader = DictLoader(dict(importme=trusted.tag(
        "{% set hi_from='imported template local' %}"
        "{% macro validate_this() %}"
        "{{ " + validate_me + " }}"
        "{% endmacro %}"
    )))

    # The template-local variable hi_from should mask the one passed in; it currently does not whenever a nested template call is made, because template locals
    # are only available in AnsibleContext.vars, and Jinja's getattr and getitem are implemented on (Ansible)Environment, which are context-agnostic. We're
    # hopeful this could be supported by Jinja in the future, at which point we can implement template-local var propagation to nested Templars/template calls.
    # The getitem/getattr calls would need to be implemented on (Ansible)Context, or otherwise gain the ability to consult the context vars to safely
    # propagate locals. A ContextVar is insufficient to handle this problem with a new context, since the possibility of overlapping contexts from
    # abandoned-but-not-closed generators is real. PEP568 would solve this problem, if it's ever implemented...
    res = templar.template(trusted.tag(
        "{% set hi_from='template local' %}"
        "{% from 'importme' import validate_this with context %}"
        "{{ " + validate_me + " + validate_this() }}"
    ))

    assert res == [
        "template local",
        "template local",
        "template local",
        dict(templated_scalar="template local"),
        "imported template local",
        "template local",
        "template local",
        dict(templated_scalar="template local"),
    ]


@pytest.mark.parametrize("key", _TEMPLATE_OVERRIDE_FIELD_NAMES)
def test_template_overrides_defaults(key: str) -> None:
    overrides = TemplateOverrides()
    env = AnsibleEnvironment()

    assert getattr(overrides, key) == getattr(env, key)


@pytest.mark.parametrize("value, expected_overrides", [
    ("#jinja2:newline_sequence:'\\r\\n'\n", TemplateOverrides(newline_sequence='\r\n')),
    ("#jinja2:trim_blocks:False\n", TemplateOverrides(trim_blocks=False)),
    ("#jinja2:line_statement_prefix:None\n{{'template constant'}}\n{{'another'}}\n", TemplateOverrides.DEFAULT),
    ("#jinja2:line_statement_prefix:'!!'\n{{'template constant'}}\n{{'another'}}\n", TemplateOverrides(line_statement_prefix="!!")),
], ids=lambda value: repr(value.overlay_kwargs() if isinstance(value, TemplateOverrides) else value))
def test_template_override_extract_success(value: str, expected_overrides: TemplateOverrides):
    expected_template = value.split('\n', maxsplit=1)[1]
    template, overrides = TemplateOverrides.DEFAULT._extract_template_overrides(value)

    assert template == expected_template
    assert overrides == expected_overrides


@pytest.mark.parametrize("value", [
    "#jinja2:newline_sequence:'\\n\\r'\n",
    "#jinja2:bogus_key:''\n",
    "#jinja2:variable_start_string:2\n",
    "#jinja2:variable_start_string:'{{'",
    "#jinja2:variable_start_string\n",
    "#jinja2:\n",
    "#jinja2:,\n",
    "#jinja2:variable_start_string:'boo',\n",
])
def test_template_override_extract_failure(value: str):
    with pytest.raises(tuple([TypeError, ValueError])):
        TemplateOverrides.DEFAULT._extract_template_overrides(value)


def test_filter_plugin_error_wrap():
    expected_error_cause = Exception("bang")

    def raises_error(_input):
        raise expected_error_cause

    templar = TemplateEngine()
    templar.environment.filters['raises_error'] = raises_error

    with pytest.raises(AnsibleTemplatePluginRuntimeError) as err:
        templar.template(TRUST.tag("{{ true | raises_error }}"))

    assert err.value.__cause__ is expected_error_cause


def test_test_plugin_error_wrap():
    expected_error_cause = Exception("bang")

    def raises_error(_input):
        raise expected_error_cause

    templar = TemplateEngine()
    templar.environment.tests['raises_error'] = raises_error

    with pytest.raises(AnsibleTemplatePluginRuntimeError) as err:
        templar.template(TRUST.tag("{{ true is raises_error }}"))

    assert err.value.__cause__ is expected_error_cause


def test_lookup_plugin_error_wrap(mocker: pytest_mock.MockerFixture):
    expected_error_cause = Exception("bang")

    from ansible.plugins.lookup import LookupBase

    class RaisesError(LookupBase):
        def run(self, _input, *args, **kwargs):
            raise expected_error_cause

    def mock_lookup_get(name, *args, **kwargs) -> t.Any:
        return RaisesError()

    templar = TemplateEngine()
    mock_lookup_loader = mocker.MagicMock()
    mock_lookup_loader.get = mock_lookup_get

    mocker.patch.object(_jinja_plugins, 'lookup_loader', mock_lookup_loader)

    with pytest.raises(AnsibleTemplatePluginRuntimeError) as err:
        templar.template(TRUST.tag("{{ lookup('raises_error') }}"))

    assert err.value.__cause__ is expected_error_cause


ok = "ok"
undefined_with_unsafe = AnsibleUndefinedVariable("is unsafe")


@pytest.mark.parametrize("expr, expected", (
    ('on_dict["_native_copy"]', ok),  # [] prefers getitem, matching dict key present (no attr lookup)
    ('on_dict._native_copy', ok),  # . matches `_` prefixed` method on _AnsibleTaggedDict, custom fallback to getitem with valid key
    ('on_dict["get"]', ok),  # [] prefers getitem, matching dict key present (no attr lookup)
    ('on_dict.get("_native_copy")', ok),  # . matches safe method on dict, should be callable to fetch a valid key
    ('on_dict["clear"]', ok),  # [] prefers getitem, matching dict key present (no attr lookup)
    ('on_dict["_non_method_or_attr"]', ok),  # [] prefers getitem, sunder key ok
    ('on_dict._non_method_or_attr', ok),  # . finds nothing, getattr fallback finds dict key, `_` prefix has no effect
    ('on_list._native_copy', undefined_with_unsafe),  # . matches sunder-named method on list, fails
    ('on_list["_native_copy"]', undefined_with_unsafe),  # [] gets TypeError, getattr fallback matches sunder-named method on list, fails
    ('on_list.0', 42),  # . gets AttributeError, getitem fallback succeeds
    ('on_list[0]', 42),  # [] prefers getitem, succeeds
    # -- Jinja mutable method sandbox test cases follow; if sandbox is re-enabled, the correct behavior is defined by the commented value below
    ('on_dict.clear | type_debug', 'builtin_function_or_method'),
    # ('on_dict.clear', ok),  # . matches known-mutating method on _AnsibleTaggedDict, custom fallback to getitem with valid key
    ('on_dict["setdefault"] | type_debug', 'method'),
    # ('on_dict.setdefault', undefined_with_unsafe),  # . finds a known-mutating method, getitem fallback finds no matching dict key, fails
    ('on_list.sort | type_debug', 'method'),
    # ('on_list.sort', undefined_with_unsafe),  # . matches known-mutating method on list, fails
    ('on_list["sort"] | type_debug', 'method'),
    # ('on_list["sort"]', undefined_with_unsafe),  # [] gets TypeError, getattr fallback matches known-mutating method on list, fails
))
def test_jinja_getattr(expr: str, expected: object) -> None:
    """Validate expected behavior from Jinja environment getattr/getitem methods, including Ansible-customized fallback behavior."""
    assert AnsibleTaggedObject._native_copy  # validate that the underlying type has the method we're expecting to collide with

    templar = TemplateEngine(variables=dict(
        on_dict=dict(
            _native_copy=ok,  # same key as sunder method
            get=ok,  # same key as a safe method
            clear=ok,  # same key as an unsafe method
            _non_method_or_attr=ok,  # key with sunder prefix, no matching method
        ),
        on_list=[42],
    ))

    with (pytest.raises(type(expected), match=expected.message) if isinstance(expected, AnsibleUndefinedVariable) else nullcontext()):
        result = templar.evaluate_expression(TRUST.tag(expr))
        assert result == expected


def test_defer_template_error_from_marker(marker: Marker) -> None:
    """Verify that deferring a Marker returns its source."""
    with pytest.raises(MarkerError) as error:
        raise MarkerError('', marker)

    result = defer_template_error(error.value, None, is_expression=False)

    assert result is marker


def test_defer_template_error_from_exception(template_context: TemplateContext) -> None:
    """Verify that deferring an Exception not derived from AnsibleTemplateError returns a CapturedExceptionMarker wrapping an AnsibleTemplateError."""
    with pytest.raises(Exception) as error:
        raise Exception()

    result = defer_template_error(error.value, None, is_expression=False)

    assert isinstance(result, CapturedExceptionMarker)
    assert isinstance(result._marker_captured_exception, AnsibleTemplateError)
    assert result._marker_captured_exception.__cause__ is error.value


def test_defer_template_error_from_ansible_template_error(template_context: TemplateContext) -> None:
    """Verify that deferring an AnsibleTemplateError returns a CapturedExceptionMarker wrapping that exception."""
    with pytest.raises(AnsibleTemplateError) as error:
        raise AnsibleTemplateError()

    result = defer_template_error(error.value, None, is_expression=False)

    assert isinstance(result, CapturedExceptionMarker)
    assert result._marker_captured_exception is error.value


def test_defer_template_requires_traceback(template_context: TemplateContext):
    """Verify that deferring an exception that has not been raised results in an AssertionError."""
    with pytest.raises(AssertionError, match='ex must be a previously raised exception'):
        # an exception without a traceback should be rejected with an AssertionError
        defer_template_error(AnsibleTemplateError(), None, is_expression=False)


@pytest.fixture
def mock_breakpointhook(mocker: pytest_mock.MockerFixture) -> t.Iterator[unittest.mock.Mock]:
    """Yields a Mock object patched on `sys.breakpointhook` (causes explicit `breakpoint()` calls to no-op)."""
    breakpointhook = mocker.Mock()

    mocker.patch.object(sys, 'breakpointhook', breakpointhook)

    yield breakpointhook


@pytest.fixture(params=(True, False))
def debuggable_templar(request: pytest.FixtureRequest, tmp_path: pathlib.Path) -> TemplateEngine:
    """Multiplying parameterized fixture that yields a Templar with template source debugging force-enabled and force-disabled."""
    templar = TemplateEngine()

    env = templar.environment
    env._debuggable_template_source = request.param
    env._debuggable_template_source_path = tmp_path

    return templar


@pytest.mark.parametrize("expression", (
    'templar.environment.get_template("importme")',
    'templar.environment.from_string("{{ 42 }}")',
    'templar.environment.compile_expression("42")._template',
))
def test_template_source_debug(expression: str, debuggable_templar: TemplateEngine, mock_breakpointhook: unittest.mock.Mock):
    """Ensures that template source debug support creates source files and sets debugger support attributes correctly."""
    debuggable_templar.environment.loader = DictLoader(dict(importme=TRUST.tag('{{ 42 }}')))

    template: AnsibleTemplate = eval(expression, globals(), dict(templar=debuggable_templar))

    debug_enabled = debuggable_templar.environment._debuggable_template_source

    if debug_enabled:
        assert template.root_render_func.__code__.co_filename == template.filename
        assert pathlib.Path(template.filename).exists()
    else:
        assert template.filename == '<template>'

    assert mock_breakpointhook.called == debug_enabled


@pytest.mark.parametrize("kwargs, expected", (
    ({}, TemplateOverrides.DEFAULT),
    (dict(variable_start_string="{{"), TemplateOverrides.DEFAULT),
    (dict(variable_start_string="!!"), TemplateOverrides(variable_start_string="!!")),
), ids=lambda arg: str(arg) if isinstance(arg, dict) else "TemplateOverrides")
def test_template_overrides_from_kwargs(kwargs: dict[str, t.Any], expected: TemplateOverrides) -> None:
    result = TemplateOverrides.from_kwargs(kwargs)

    if expected is TemplateOverrides.DEFAULT:
        assert result is expected
    else:
        assert result == expected


@pytest.mark.parametrize("name", _BUILTIN_TEST_ALIASES)
def test_builtin_alt_names(name: str) -> None:
    """Verify that Jinja2 plugin alternate names are valid."""
    tests = AnsibleEnvironment.__mro__[1]().tests
    alt_name = _BUILTIN_TEST_ALIASES[name]

    assert tests[name] is tests[alt_name]


@pytest.mark.parametrize("template,variables,expected", (
    # macro getting an undefined from a getitem should continue execution
    (
        "{{ macro_user('badkey') }}",
        dict(data={}, macro_user=TRUST.tag("{% macro a_macro(a_key) %}{{ data[a_key] | default('thedefault') }}{% endmacro %}{{ a_macro }}")),
        "thedefault",
    ),
    # call block getting an undefined from a getitem should continue execution
    (
        "{% macro a_macro() %}it was {{ caller() }}{% endmacro %}{% call a_macro() %}{{ data['nope'] | default('thedefault') }}{% endcall %}",
        dict(data={}),
        "it was thedefault",
    ),
    # macro receiving an undefined arg should always execute
    (
        "{{ macro_user(an_undefined_var) }}",
        dict(data={}, macro_user=TRUST.tag("{% macro a_macro(value) %}{{ value | default('thedefault') }}{% endmacro %}{{ a_macro }}")),
        "thedefault",
    ),
))
def test_macro_marker_handling(template: str, variables: dict[str, object], expected: object) -> None:
    """
    Ensure that `JinjaCallContext` Marker handling is masked/set correctly for Jinja macro callables.
    Jinja's generated macro code handles Markers, so pre-emptive raise on retrieval should be disabled for the macro `call()`.
    """
    res = TemplateEngine(variables=variables).template(TRUST.tag(template))

    assert res == expected


@pytest.mark.parametrize("expression, result", (
    ("(0x20).__or__(0xf)", 47),
    ("(0x20).__and__(0x29)", 32),
    ("(0x20).__lshift__(1)", 64),
    ("(0x20).__rshift__(1)", 16),
    ("(0x20).__xor__(0x29)", 9),
))
def test_bitwise_dunder_methods(expression: str, result: object) -> None:
    """
    Verify a limited set of dunder methods are supported.
    This feature may be deprecated and removed in the future after bitwise filters are implemented.
    """
    assert TemplateEngine().evaluate_expression(TRUST.tag(expression)) == result


@pytest.mark.parametrize("expression", (
    "{1:2}.__delitem__(1)",
    "[123].__len__()",
))
def test_disallowed_dunder_methods(expression: str) -> None:
    """Verify dunder methods are disallowed by the Jinja sandbox."""
    with pytest.raises(AnsibleUndefinedVariable, match="is unsafe"):
        TemplateEngine().evaluate_expression(TRUST.tag(expression))


@pytest.mark.parametrize("template, result", (
    ("{% set my_list = [] %}{% set _ = my_list.append(1) %}{{ my_list }}", [1]),
    ("{% set my_list = [] %}{% set _ = my_list.extend([1, 2]) %}{{ my_list }}", [1, 2]),
    ("{% set my_dict = {} %}{% set _ = my_dict.update(a=1) %}{{ my_dict }}", dict(a=1)),
))
def test_mutation_methods(template: str, result: object) -> None:
    """
    Verify mutation methods are allowed by the Jinja sandbox.
    This feature may be deprecated and removed in a future release by using Jinja's ImmutableSandboxedEnvironment.
    """
    assert TemplateEngine().template(TRUST.tag(template)) == result


class ExampleMarkerAccessTracker(NotifiableAccessContextBase):
    def __init__(self) -> None:
        self._type_interest = frozenset(Marker._concrete_subclasses)
        self._markers: list[Marker] = []

    def _notify(self, o: Marker) -> None:
        self._markers.append(o)


@pytest.mark.parametrize("template", (
    '{{ adict["bogus"] | default("ok") }}',
    '{{ adict.bogus | default("ok") }}',
))
def test_marker_access_getattr_and_getitem(template: str) -> None:
    """Ensure that getattr and getitem always access markers."""
    # the absence of a JinjaCallContext should cause the access done by getattr and getitem not to trip when a marker is encountered
    assert TemplateEngine(variables=dict(adict={})).template(TRUST.tag(template)) == "ok"

    with ExampleMarkerAccessTracker() as tracker:  # the access done by getattr and getitem should immediately trip when a marker is encountered
        TemplateEngine(variables=dict(adict={})).template(TRUST.tag(template))

    assert type(tracker._markers[0]) is UndefinedMarker  # pylint: disable=unidiomatic-typecheck
