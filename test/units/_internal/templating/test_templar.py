# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import itertools
import pathlib
import sys

import unittest.mock
import typing as t

import pytest_mock

from jinja2.runtime import Context
from jinja2.loaders import DictLoader

import unittest

from ansible._internal import _display_utils
from ansible._internal._templating._datatag import _JinjaConstTemplate
from ansible.errors import (
    AnsibleError, AnsibleUndefinedVariable, AnsibleTemplateSyntaxError, AnsibleBrokenConditionalError, AnsibleTemplateError, AnsibleTemplateTransformLimitError,
    TemplateTrustCheckFailedError,
)
from ansible._internal._templating._errors import AnsibleTemplatePluginRuntimeError, AnsibleTemplatePluginLoadError, AnsibleTemplatePluginNotFoundError
from ansible._internal._errors._handler import ErrorAction, ErrorHandler
from ansible.module_utils._internal._datatag import AnsibleTagHelper, AnsibleDatatagBase
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible._internal._templating import _transform
from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.plugins.loader import init_plugin_loader
from ansible._internal._templating._jinja_common import _TemplateConfig, _SandboxMode
from ansible._internal._templating._jinja_plugins import _lookup
from ansible._internal._templating import _jinja_plugins
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible._internal._templating._jinja_bits import AnsibleEnvironment, AnsibleContext, is_possibly_template, is_possibly_all_template
from ansible._internal._templating._marker_behaviors import ReplacingMarkerBehavior
from ansible._internal._templating._utils import TemplateContext
from ansible.module_utils._internal import _event_utils
from ansible.utils.display import Display
from units.mock.loader import DictDataLoader
from units.test_utils.controller.display import emits_warnings

import pytest

TRUST = TrustedAsTemplate()

origin = Origin(path="/some/path/for/testing", line_num=1, col_num=2)


class BaseTemplar(object):
    def setUp(self):
        init_plugin_loader()
        self.test_vars = dict(
            foo="bar",
            bam=TrustedAsTemplate().tag("{{foo}}"),
            num=1,
            var_true=True,
            var_false=False,
            var_dict=dict(a="b"),
            bad_dict="{a='b'",
            var_list=[1],
            recursive=TrustedAsTemplate().tag("{{recursive}}"),
            some_var="blip",
            some_keyword=TrustedAsTemplate().tag("{{ foo }}"),
            some_unsafe_var="unsafe_blip",
            some_unsafe_keyword=TrustedAsTemplate().tag("{{ foo }}"),
            str_with_error=TrustedAsTemplate().tag("{{ 'str' | from_json }}"),
            template_dict={TrustedAsTemplate().tag("{{ a_keyword }}"): TrustedAsTemplate().tag("{{ some_var }}")},
            template_var=TrustedAsTemplate().tag('{{ some_var }}'),
        )
        self.fake_loader = DictDataLoader({
            "/path/to/my_file.txt": "foo\n",
        })
        self.templar = TemplateEngine(loader=self.fake_loader, variables=self.test_vars)
        self._ansible_context = AnsibleContext(self.templar.environment, {}, {}, {})

    def tearDown(self):
        _AnsibleCollectionFinder._remove()
        nuke_module_prefix('ansible_collections')


class TestTemplarTemplate(BaseTemplar, unittest.TestCase):
    def test_trust_fail_raises_in_tests(self):
        """Ensure template trust check failures default to fatal for unit tests (set in units/conftest.py)"""
        from ansible._internal._templating._engine import TemplateTrustCheckFailedError

        assert _TemplateConfig.untrusted_template_handler.action is ErrorAction.ERROR

        with pytest.raises(TemplateTrustCheckFailedError):
            self.templar.template("{{ i_am_not_trusted }}")

    def test_trust_fail_warning_behavior(self):
        """Validate that trust checks are non-fatal when TemplateConfig.untrusted_template_handler is set to `ErrorAction.WARNING`."""
        untrusted_template = "{{ i_am_not_trusted }}"

        assert hasattr(_TemplateConfig, 'untrusted_template_handler')

        with (unittest.mock.patch.object(_TemplateConfig, 'untrusted_template_handler', ErrorHandler(ErrorAction.WARNING)),
              unittest.mock.patch.object(Display, 'error_as_warning', return_value=None) as mock_warning):
            assert self.templar.template(untrusted_template) is untrusted_template

        assert mock_warning.call_count > 0
        warning_value = mock_warning.call_args.kwargs['exception']
        assert isinstance(warning_value, TemplateTrustCheckFailedError)
        assert "Encountered untrusted template or expression" in warning_value.message
        assert warning_value.obj == untrusted_template

    def test_is_possible_template(self):
        """This test ensures that a broken template still gets templated"""
        # Purposefully invalid jinja
        self.assertRaises(AnsibleError, self.templar.template, TrustedAsTemplate().tag('{{ foo|default(False)) }}'))

    def test_is_template_raw_string(self):
        res = self.templar.is_template('foo')
        self.assertFalse(res)

    def test_is_template_none(self):
        res = self.templar.is_template(None)
        self.assertFalse(res)

    def test_template(self):
        res = self.templar.template(TrustedAsTemplate().tag('{{foo}}'))
        self.assertTrue(res)
        self.assertEqual(res, 'bar')

    def test_template_in_data(self):
        res = self.templar.template(TrustedAsTemplate().tag('{{bam}}'))
        self.assertTrue(res)
        self.assertEqual(res, 'bar')

    def test_template_bare(self):
        res = self.templar.template('bam')
        self.assertTrue(res)
        self.assertEqual(res, 'bam')

    def test_template_to_json(self):
        res = self.templar.template(TrustedAsTemplate().tag('{{bam|to_json}}'))
        self.assertTrue(res)
        self.assertEqual(res, '"bar"')

    def test_template_untagged_string(self):
        unsafe_obj = "Hello"
        res = self.templar.template(unsafe_obj)
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_weird(self):
        data = TrustedAsTemplate().tag(u"""1 2 #}huh{# %}ddfg{% }}dfdfg{{  {%what%} {{#foo#}} {%{bar}%} {#%blip%#} {{asdfsd%} 3 4 {{foo}} 5 6 7""")
        self.assertRaisesRegex(AnsibleError,
                               'Syntax error in template',
                               self.templar.template,
                               data)

    def test_template_with_error(self):
        """Check that AnsibleError is raised, fail if an unhandled exception is raised"""
        self.assertRaises(AnsibleError, self.templar.template, TrustedAsTemplate().tag("{{ str_with_error }}"))


class TestTemplarMisc(BaseTemplar, unittest.TestCase):
    def test_templar_simple(self):

        templar = self.templar
        # test some basic templating
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{foo}}")), "bar")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{foo}}\n")), "bar\n")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{foo}}\n"), options=TemplateOptions(preserve_trailing_newlines=True)), "bar\n")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{foo}}\n"), options=TemplateOptions(preserve_trailing_newlines=False)), "bar")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{bam}}")), "bar")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{num}}")), 1)
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{var_true}}")), True)
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{var_false}}")), False)
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{var_dict}}")), dict(a="b"))
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{bad_dict}}")), "{a='b'")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{var_list}}")), [1])

        # force errors
        self.assertRaises(AnsibleUndefinedVariable, templar.template, TrustedAsTemplate().tag("{{bad_var}}"))
        self.assertRaises(AnsibleUndefinedVariable, templar.template, TrustedAsTemplate().tag("{{lookup('file', bad_var)}}"))
        self.assertRaises(AnsibleError, templar.template, TrustedAsTemplate().tag("{{lookup('bad_lookup')}}"))
        self.assertRaises(AnsibleError, templar.template, TrustedAsTemplate().tag("{{recursive}}"))
        self.assertRaises(AnsibleUndefinedVariable, templar.template, TrustedAsTemplate().tag("{{foo-bar}}"))

        result = templar.extend(marker_behavior=ReplacingMarkerBehavior()).template(TrustedAsTemplate().tag("{{bad_var}}"))
        assert "<< error 1 - 'bad_var' is undefined >>" in result

        # test setting available_variables
        templar.available_variables = dict(foo="bam")
        self.assertEqual(templar.template(TrustedAsTemplate().tag("{{foo}}")), "bam")

    def test_templar_escape_backslashes(self):
        # Rule of thumb: If escape backslashes is True you should end up with
        # the same number of backslashes as when you started.
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\t{{foo}}"), options=TemplateOptions(escape_backslashes=True)), "\tbar")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\t{{foo}}"), options=TemplateOptions(escape_backslashes=False)), "\tbar")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo}}"), options=TemplateOptions(escape_backslashes=True)), "\\bar")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo}}"), options=TemplateOptions(escape_backslashes=False)), "\\bar")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\t' }}"), options=TemplateOptions(escape_backslashes=True)), "\\bar\t")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\t' }}"), options=TemplateOptions(escape_backslashes=False)), "\\bar\t")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\\t' }}"), options=TemplateOptions(escape_backslashes=True)), "\\bar\\t")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\\t' }}"), options=TemplateOptions(escape_backslashes=False)), "\\bar\t")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\\\\t' }}"), options=TemplateOptions(escape_backslashes=True)), "\\bar\\\\t")
        self.assertEqual(self.templar.template(TrustedAsTemplate().tag("\\{{foo + '\\\\t' }}"), options=TemplateOptions(escape_backslashes=False)), "\\bar\\t")


class TestTemplarLookup(BaseTemplar, unittest.TestCase):
    @staticmethod
    def lookup(name: str, /, *args, **kwargs) -> t.Any:
        with TemplateContext(template_value=None, templar=TemplateEngine(), options=TemplateOptions(), stop_on_template=False):
            return _lookup(name, *args, **kwargs)

    def test_lookup_missing_plugin(self):
        self.assertRaisesRegex(AnsibleTemplatePluginNotFoundError,
                               "The lookup plugin 'not_a_real_lookup_plugin' was not found.",
                               self.lookup,
                               'not_a_real_lookup_plugin',
                               'an_arg', a_keyword_arg='a_keyword_arg_value')

    def test_lookup_list(self):
        res = self.lookup('list', 'an_arg', 'another_arg')
        self.assertEqual(res, 'an_arg,another_arg')

    def test_lookup_jinja_undefined(self):
        self.assertRaisesRegex(AnsibleUndefinedVariable,
                               "'an_undefined_jinja_var' is undefined",
                               self.templar.template,
                               TrustedAsTemplate().tag('{{ lookup("list", an_undefined_jinja_var) }}'))

    def test_lookup_jinja_defined(self):
        res = self.lookup('list', 'x')
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_dict_string_passed(self):
        self.assertRaisesRegex(AnsibleError,
                               "lookup plugin expects a dictionary",
                               self.lookup,
                               'dict',
                               'x')

    def test_lookup_jinja_dict_list_passed(self):
        self.assertRaisesRegex(AnsibleError,
                               "lookup plugin expects a dictionary",
                               self.lookup,
                               'dict',
                               ['foo', 'bar'])

    def test_lookup_jinja_kwargs(self):
        res = self.lookup('list', 'blip', random_keyword='12345')
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_list_wantlist(self):
        res = self.templar.template(TrustedAsTemplate().tag("{{ lookup('list', template_var, wantlist=True) }}"))
        self.assertEqual(res, ["blip"])

    def test_lookup_jinja_list_wantlist_undefined(self):
        self.assertRaisesRegex(AnsibleUndefinedVariable,
                               "'some_undefined_var' is undefined",
                               self.templar.template,
                               TrustedAsTemplate().tag('{{ lookup("list", some_undefined_var, wantlist=True) }}'))

    def test_lookup_jinja_list_wantlist_unsafe(self):
        res = self.lookup('list', 'x', wantlist=True)
        for lookup_result in res:
            assert not TrustedAsTemplate.is_tagged_on(lookup_result)

        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_dict(self):
        res = self.templar.template(TrustedAsTemplate().tag('{{ lookup("list", template_dict) }}'))
        self.assertEqual(res['{{ a_keyword }}'], "blip")
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_dict_unsafe(self):
        res = self.lookup('list', {'x': 'x'})
        assert not TrustedAsTemplate.is_tagged_on(res['x'])
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_dict_unsafe_value(self):
        res = self.lookup('list', {'x': 'x'})
        assert not TrustedAsTemplate.is_tagged_on(res['x'])
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_lookup_jinja_none(self):
        res = self.lookup('list', None)
        self.assertIsNone(res)


class TestAnsibleContext(BaseTemplar, unittest.TestCase):
    def _context(self, variables=None):
        variables = variables or {}

        env = AnsibleEnvironment()
        context = AnsibleContext(env, parent={}, name='some_context',
                                 blocks={})

        for key, value in variables.items():
            context.vars[key] = value

        return context

    def test(self):
        context = self._context()
        self.assertIsInstance(context, AnsibleContext)
        self.assertIsInstance(context, Context)

    def test_resolve_unsafe(self):
        context = self._context(variables={'some_unsafe_key': 'some_unsafe_string'})
        res = context.resolve('some_unsafe_key')
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_resolve_unsafe_list(self):
        context = self._context(variables={'some_unsafe_key': ['some unsafe string 1']})
        res = context.resolve('some_unsafe_key')
        assert not TrustedAsTemplate.is_tagged_on(res[0])
        assert not TrustedAsTemplate.is_tagged_on(res)

    def test_resolve_unsafe_dict(self):
        context = self._context(variables={'some_unsafe_key':
                                           {'an_unsafe_dict': 'some unsafe string 1'}
                                           })
        res = context.resolve('some_unsafe_key')
        assert not TrustedAsTemplate.is_tagged_on(res['an_unsafe_dict'])

    def test_resolve(self):
        context = self._context(variables={'some_key': 'some_string'})
        res = context.resolve('some_key')
        self.assertEqual(res, 'some_string')

    def test_resolve_none(self):
        context = self._context(variables={'some_key': None})
        res = context.resolve('some_key')
        self.assertEqual(res, None)


def test_unsafe_lookup():
    res = TemplateEngine(
        None,
        variables={
            'var0': TrustedAsTemplate().tag('{{ var1 }}'),
            'var1': ['unsafe'],
        }
    ).template(TrustedAsTemplate().tag('{{ lookup("list", var0) }}'))
    assert not TrustedAsTemplate.is_tagged_on(res[0])


def test_unsafe_lookup_no_conversion():
    res = TemplateEngine(
        None,
        variables={
            'var0': TrustedAsTemplate().tag('{{ var1 }}'),
            'var1': ['unsafe'],
        }
    ).template(
        TrustedAsTemplate().tag('{{ lookup("list", var0) }}'),
    )
    assert not TrustedAsTemplate.is_tagged_on(res)


@pytest.mark.parametrize("tagged", (
    False,
    True,
))
def test_dict_template(tagged: bool) -> None:
    """Verify that templar.template can round-trip both tagged and untagged values in a dict."""
    key1 = "key1"
    val1 = "val1"

    if tagged:
        key1 = origin.tag(key1)
        val1 = origin.tag(val1)

    test1 = {
        key1: val1,
    }

    variables = dict(
        test1=test1,
    )

    templar = TemplateEngine(variables=variables)

    result = templar.template(TrustedAsTemplate().tag('{{test1}}'))

    assert result == test1
    assert AnsibleTagHelper.tags(result) == AnsibleTagHelper.tags(test1)


@pytest.mark.parametrize("expr,expected,variables", [
    ("'constant'", "constant", None),
    ("a - b", 42, dict(a=100, b=58)),
])
def test_evaluate_expression(expr: str, expected: t.Any, variables: dict[str, t.Any] | None):
    assert TemplateEngine(variables=variables).evaluate_expression(TRUST.tag(expr)) == expected


@pytest.mark.parametrize("expr,error_type", [
    ("fhdgsfk#$76&@#$&", AnsibleTemplateSyntaxError),
    ("bogusvar", AnsibleUndefinedVariable),
    ("untrusted expression", TemplateTrustCheckFailedError),
    (dict(hi="{{'mom'}}"), TypeError),
])
def test_evaluate_expression_errors(expr: str, error_type: type[Exception]):
    if error_type is not TemplateTrustCheckFailedError:
        expr = TRUST.tag(expr)

    with pytest.raises(error_type):
        TemplateEngine().evaluate_expression(expr)


@pytest.mark.parametrize("conditional,expected,variables", [
    ("1 == 2", False, None),
    ("test2_name | default(True)", True, None),
    # DTFIX5: more success cases?
])
def test_evaluate_conditional(conditional: str, expected: t.Any, variables: dict[str, t.Any] | None):
    assert TemplateEngine().evaluate_conditional(TRUST.tag(conditional)) == expected


@pytest.mark.parametrize("conditional,error_type", [
    ("fkjhs$#@^%$*& ldfkjds", AnsibleTemplateSyntaxError),
    ("#jinja2:variable_start_string:2\n{{blah}}", AnsibleTemplateSyntaxError),
    ("#jinja2:bogus_key:'val'\n{{blah}}", AnsibleTemplateSyntaxError),
    ("bogusvar", AnsibleUndefinedVariable),
    ("not trusted", TemplateTrustCheckFailedError),
])
def test_evaluate_conditional_errors(conditional: t.Any, error_type: type[Exception], mocker: pytest_mock.MockerFixture):
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)  # force this on since a number of cases need it

    if error_type is not TemplateTrustCheckFailedError:
        conditional = TRUST.tag(conditional)

    with pytest.raises(error_type):
        TemplateEngine().evaluate_conditional(conditional)


@pytest.mark.parametrize("value", (
    '{{ foo }}',
    '{% foo %}',
    '{# foo #}',
    '{# {{ foo }} #}',
    '{# {{ nothing }} {# #}',
    '{# {{ nothing }} {# #} #}',
    '{% raw %}{{ foo }}{% endraw %}',
    # in 2.16 and earlier these were not considered templates due to syntax errors
    # now syntax errors in templates are still reported as templates, since is_template no longer compiles the template
    '{{ foo',
    '{% foo',
    '{# foo',
    '{{ foo %}',
    '{{ foo #}',
    '{% foo }}',
    '{% foo #}',
    '{# foo %}',
    '{# foo }}',
    '{{ foo {{',
    '{% raw %}{% foo %}',
))
def test_is_template_true(value: str) -> None:
    assert TemplateEngine().is_template(TRUST.tag(value))


@pytest.mark.parametrize("value", (
    'foo',
))
def test_is_template_false(value: str) -> None:
    assert not TemplateEngine().is_template(TRUST.tag(value))


@pytest.mark.parametrize("value", (
    '{{ foo }}',
    '{% foo %}',
    '{# foo #}',
    '{# {{ foo }} #}',
    '{# {{ nothing }} {# #}',
    '{# {{ nothing }} {# #} #}',
    '{% raw %}{{ foo }}{% endraw %}',
    '{{',
    '{%',
    '{#',
    '{% raw',
))
def test_is_possibly_template_true(value: str) -> None:
    assert is_possibly_template(value)


@pytest.mark.parametrize("value", (
    '{',
    '%',
    '#',
    'foo',
    '}}',
    '%}',
    'raw %}',
    '#}',
))
def test_is_possibly_template_false(value: str) -> None:
    assert not is_possibly_template(value)


def test_stop_on_container() -> None:
    # DTFIX5: add more test cases
    assert TemplateEngine().resolve_to_container(TRUST.tag('{{ [ 1 ] }}')) == [1]


@pytest.mark.parametrize("value", [True, False])
def test_stripped_conditionals(value: bool, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)  # force this on since this case needs it

    assert TemplateEngine().evaluate_conditional(TRUST.tag(f"""\n \r\n \t{{{{ {value} }}}} \n\n  \t \t\t  """)) == value


@pytest.mark.parametrize("template, variables, error", (
    ("{{ undefined_var.undefined_attribute }}", {}, "'undefined_var' is undefined >>"),
    ("{{ some_dict['undefined_key'] }}", dict(some_dict={}), "object of type 'dict' has no attribute 'undefined_key' >>"),
    ("{{ some_dict.undefined_key }}", dict(some_dict={}), "object of type 'dict' has no attribute 'undefined_key' >>"),
    ("{{ m1 }} {{ m2 }} here", {}, "<< error 1 - 'm1' is undefined >> << error 2 - 'm2' is undefined >> here"),
    ("before {{ m1 + m2 }} after", {}, "before << error 1 - 'm1' is undefined >><< error 2 - template potentially truncated >>"),
))
def test_jinja_sourced_undefined(template: str, variables: dict[str, t.Any], error: str) -> None:
    """
    Ensure when Jinja encounters a `Marker` and raises `MarkerError`,
    that we turn it back into the original `Marker` so marker_behavior can handle it during finalization.
    """
    assert error in TemplateEngine(variables=variables, marker_behavior=ReplacingMarkerBehavior()).template(TRUST.tag(template))


def test_omit_concat() -> None:
    assert TemplateEngine().template(TRUST.tag("{{ omit }}hi{{ omit }} mom")) == 'hi mom'


@pytest.mark.parametrize("conditional", (
    # Jinja plugins
    "'join' is filter",
    "'join' is not test",
    "'eq' is test",
    "'eq' is not filter",

    # Ansible plugins
    "'comment' is filter",
    "'comment' is not test",
    "'version' is test",
    "'version' is not filter",

    # plugin not found
    "'nope' is not filter",
    "'nope' is not test",
))
def test_plugin_found_not_found(conditional: str) -> None:
    assert TemplateEngine().evaluate_conditional(TRUST.tag(conditional))


@pytest.mark.parametrize("value, expected", (
    ("{{ {'a': 1}.items() }}", [['a', 1]]),
    ("{{ {'a': 1}.keys() }}", ['a']),
    ("{{ {'a': 1}.values() }}", [1]),
    ("{{ yielder(2) }}", [0, 1]),
    ("{% set y = yielder(2) %}{{ y | list }} | {{ y | list }}", "[0, 1] | [0, 1]"),
), ids=str)
def test_finalize_generator(value: t.Any, expected: t.Any) -> None:
    def yielder(count: int) -> t.Generator[int, None, None]:
        yield from range(count)

    templar = TemplateEngine(variables=dict(
        yielder=yielder,
    ))

    # DTFIX5: we still need to deal with the "Encountered unsupported" warnings these generate
    assert templar.template(TRUST.tag(value)) == expected


@pytest.mark.parametrize("template", (
    "{{ lookup('my_lookup', some_var) }}",
    "{{ some_var | my_filter }}",
    "{{ some_var is my_test }}",
))
def test_eager_trip_undefined(template: str, mocker: pytest_mock.MockerFixture) -> None:
    """Verify that eager tripping of Marker works for template plugins which only perform isinstance checks on undefined values."""
    from ansible.plugins.lookup import LookupBase

    class MyLookup(LookupBase):
        def run(self, terms, variables=None, **kwargs):
            return [isinstance(value, bool) for value in itertools.chain(*terms)]

    def my_filter(values):
        return [isinstance(value, bool) for value in values]

    def my_test(values):
        return all(isinstance(value, bool) for value in values)

    def mock_lookup_get(*_args, **_kwargs) -> t.Any:
        return MyLookup()

    mock_lookup_loader = mocker.MagicMock()
    mock_lookup_loader.get = mock_lookup_get

    mocker.patch.object(_jinja_plugins, 'lookup_loader', mock_lookup_loader)

    def get_templar(variables: dict[str, t.Any]) -> TemplateEngine:
        new_templar = TemplateEngine(variables=variables)
        new_templar.environment.filters['my_filter'] = my_filter
        new_templar.environment.tests['my_test'] = my_test

        return new_templar

    template = TRUST.tag(template)

    # verify the template works when some_var is defined

    templar = get_templar(dict(some_var=[True]))

    result = templar.template(template)

    assert result is True or result == [True]

    # verify the template raises AnsibleUndefinedVariable when some_var contains a template that references an undefined variable

    templar = get_templar(dict(some_var=[TRUST.tag("{{ nope }}")]))

    with pytest.raises(AnsibleUndefinedVariable) as ex:
        templar.template(template)

    assert ex.value.message == "'nope' is undefined"


def as_template(value: str) -> str:
    return f"{{{{ {value} }}}}"


TEMPLATED_LOOKUP_NAME_TEST_VALUES = [
    ("""lookup('{{ "pipe" }}', 'echo hi')""", "hi"),
    ("""query('{{ "pipe" }}', 'echo hi')""", ["hi"]),
]


@pytest.mark.parametrize("value", [v[0] for v in TEMPLATED_LOOKUP_NAME_TEST_VALUES])
def test_lookup_query_name_is_not_templated_non_conditional(value: str) -> None:
    with pytest.raises(AnsibleTemplatePluginNotFoundError):
        TemplateEngine().template(TRUST.tag(as_template(value)))


@pytest.mark.parametrize("value", [v[0] for v in TEMPLATED_LOOKUP_NAME_TEST_VALUES])
def test_lookup_query_name_is_not_templated_conditional_nested_template(value: str, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)  # force this on since a number of cases need it

    with pytest.raises(AnsibleTemplatePluginNotFoundError):
        TemplateEngine().evaluate_conditional(TRUST.tag(as_template(value)))


@pytest.mark.parametrize("value, expected_result", TEMPLATED_LOOKUP_NAME_TEST_VALUES)
def test_lookup_query_name_is_not_templated_conditional_expression(value: str, expected_result: t.Any, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)  # force this on since a number of cases need it

    with emits_warnings(warning_pattern="should not contain embedded templates"):
        assert TemplateEngine().evaluate_conditional(TRUST.tag(f'{value} == {expected_result!r}'))


@pytest.mark.parametrize("value", [
    "foo(",
    "'a' == {{ 'b' }}",
])
def test_conditional_syntax_error(value: str) -> None:
    with pytest.raises(AnsibleTemplateSyntaxError):
        TemplateEngine().evaluate_conditional(TRUST.tag(value))


BROKEN_CONDITIONAL_VALUES = [
    (None, True),  # stupid backward-compat
    ("", True),  # stupid backward-compat
    ("''", False),
    ("0", False),
    ("0.0", False),
    ("1", True),
    ("1.1", True),
    ("'abc'", True),
    ("{{ '' }}", True),
    ("{{ None }}", True),
    ("{{ 0 }}", False),
    ("{{ 0.0 }}", False),
    ("{{ [] }}", False),
    ("{{ {} }}", False),
    ([], False),
    ([TRUST.tag("{{ omit }}")], False),
    ({}, False),
    (dict(a=TRUST.tag("{{ omit }}")), False),
    (["abc", TRUST.tag("{{ omit }}")], True),
    (dict(a="b", omitted=TRUST.tag("{{ omit }}")), True),
    (0, False),
    (0.0, False),
    (1, True),
    (1.1, True),
]


@pytest.mark.parametrize("value", [v[0] for v in BROKEN_CONDITIONAL_VALUES], ids=repr)
def test_broken_conditionals_disabled(value: t.Any, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_broken_conditionals', False)

    with pytest.raises(AnsibleBrokenConditionalError):
        TemplateEngine().evaluate_conditional(TRUST.tag(value))


@pytest.mark.parametrize("value, expected_result", BROKEN_CONDITIONAL_VALUES, ids=repr)
def test_broken_conditionals_enabled(value: t.Any, expected_result: bool, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_broken_conditionals', True)
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)  # force this on since a number of cases need it

    deprecation_matches = []

    if isinstance(value, str) and is_possibly_all_template(value):
        deprecation_matches.append("should not be surrounded")

    if value in (None, '', "{{ '' }}", "{{ None }}"):
        deprecation_matches.append("Empty conditional")
    else:
        deprecation_matches.append("must have a boolean result")

    with emits_warnings(deprecation_pattern=deprecation_matches):
        assert TemplateEngine().evaluate_conditional(TRUST.tag(value)) == expected_result


@pytest.mark.parametrize("template, expected", (
    ("1 == '{{ 1 }}'", False),
    ("lookup('items', '{{ [1, 2, 3] }}') == [1, 2, 3]", False),
    ("query('items', '{{ [1, 2, 3] }}') == [1, 2, 3]", False),
))
def test_embedded_templates_disabled(template: str, expected: t.Any, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', False)

    with emits_warnings(warning_pattern=[]):
        assert TemplateEngine().evaluate_conditional(TRUST.tag(template)) == expected


@pytest.mark.parametrize("template, expected", (
    ("1 == '{{ 1 }}'", True),
    ("lookup('items', '{{ [1, 2, 3] }}') == [1, 2, 3]", True),
    ("query('items', '{{ [1, 2, 3] }}') == [1, 2, 3]", True),
))
def test_embedded_templates_enabled(template: str, expected: t.Any, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch.object(_TemplateConfig, 'allow_embedded_templates', True)

    templar = TemplateEngine()

    with emits_warnings(warning_pattern="should not contain embedded templates"):
        assert templar.evaluate_conditional(TRUST.tag(template)) == expected

    # only lookup/query args support embedded templates in an actual template (not a naked expression)
    if 'lookup' in template or 'query' in template:
        with emits_warnings(warning_pattern="should not contain embedded templates"):
            assert templar.evaluate_conditional(TRUST.tag(as_template(template))) == expected


def test_available_vars_smuggling():
    """
    Jinja Template.render() and TemplateExpression.__call__() flatten their args/kwargs via splatting to dict(), which is an unnecessary copy as well as
    causing top-level templated variables to be rendered prematurely. We have some arg smuggling code to prevent this, which this test validates.
    """

    class ExplodingDict(dict):
        """A dict subclass that explodes when copied or iterated via `dict()`."""

        def __iter__(self):
            raise NotImplementedError()

        def keys(self):
            raise NotImplementedError()

    template_vars = ExplodingDict()

    # ensure our tripwire dict subclass fails when used as the source for a dict copy
    with pytest.raises(NotImplementedError):
        dict(template_vars)

    # if Jinja copies our input dict, it should blow up; assert that it doesn't and that the template renders as expected
    assert TemplateEngine(variables=template_vars).template(TRUST.tag("{{ 1 }}")) == 1


def test_template_var_isolation():
    """
    Ensure that plugin mutations to lazy-wrapped container variables do not persist outside templating.
    Direct mutation via Templar.available_variables is not currently protected (and is generally a bad idea).
    """

    orig_dict_value = dict(one="one")
    orig_list_value = [1, 2, 3]

    available_vars = dict(dict_value=orig_dict_value, list_value=orig_list_value)

    def mutate_my_vars(dict_value: dict, list_value: list) -> dict[str, t.Any]:
        dict_value["added"] = "added"
        list_value.append("added")

        return dict(dict_value=dict_value, list_value=list_value)

    res = TemplateEngine(variables=available_vars).evaluate_expression(
        TRUST.tag("mutate_my_vars(dict_value, list_value)"),
        local_variables=dict(mutate_my_vars=mutate_my_vars)
    )

    # ensure the plugin returned the mutated copies as expected
    assert res == dict(dict_value=dict(one="one", added="added"), list_value=[1, 2, 3, "added"])

    # ensure the original input variables are the same unmodified instances
    assert available_vars == dict(dict_value=dict(one="one"), list_value=[1, 2, 3])
    assert available_vars['dict_value'] is orig_dict_value
    assert available_vars['list_value'] is orig_list_value


@pytest.mark.parametrize('fixture, plugin_type, plugin_name, expected', (
    ('no_collections', 'filter', 'invalid/name.does_not_matter.also_does_not_matter', AnsibleTemplateSyntaxError),  # plugin is None
    ('no_collections', 'lookup', 'invalid/name.does_not_matter.also_does_not_matter', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'missing_namespace_name.does_not_matter.also_does_not_matter', AnsibleTemplateSyntaxError),  # KeyError
    ('no_collections', 'lookup', 'missing_namespace_name.does_not_matter.also_does_not_matter', AnsibleTemplatePluginNotFoundError),

    ('valid_collection', 'filter', 'valid.invalid/name.does_not_matter', AnsibleTemplateSyntaxError),  # KeyError
    ('valid_collection', 'lookup', 'valid.invalid/name.does_not_matter', AnsibleTemplatePluginNotFoundError),
    ('valid_collection', 'filter', 'valid.missing_collection.does_not_matter', AnsibleTemplateSyntaxError),  # KeyError
    ('valid_collection', 'lookup', 'valid.missing_collection.does_not_matter', AnsibleTemplatePluginNotFoundError),
    ('valid_collection', 'filter', 'valid.also_valid.invalid/name', AnsibleTemplateSyntaxError),  # plugin is None
    ('valid_collection', 'lookup', 'valid.also_valid.invalid/name', AnsibleTemplatePluginNotFoundError),
    ('valid_collection', 'filter', 'valid.also_valid.missing_plugin', AnsibleTemplateSyntaxError),  # plugin is None
    ('valid_collection', 'lookup', 'valid.also_valid.missing_plugin', AnsibleTemplatePluginNotFoundError),
    ('valid_collection', 'filter', 'valid.also_valid.also_also_valid', []),
    ('valid_collection', 'lookup', 'valid.also_valid.also_also_valid', []),
    ('valid_collection', 'filter', 'valid.also_valid.runtime_error', AnsibleTemplatePluginRuntimeError),
    ('valid_collection', 'lookup', 'valid.also_valid.runtime_error', AnsibleTemplatePluginRuntimeError),
    ('valid_collection', 'filter', 'valid.also_valid.load_error', AnsibleTemplatePluginLoadError),  # AnsibleError
    ('valid_collection', 'lookup', 'valid.also_valid.load_error', AnsibleTemplatePluginLoadError),
    ('valid_collection', 'template', '{% if false %}{{ 123 | valid.also_valid.load_error }}{% else %}Success{% endif %}', AnsibleTemplatePluginLoadError),

    ('no_collections', 'filter', 'ansible.invalid/name.does_not_matter', AnsibleTemplateSyntaxError),  # KeyError
    ('no_collections', 'lookup', 'ansible.invalid/name.does_not_matter', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'ansible.missing_collection.does_not_matter', AnsibleTemplateSyntaxError),  # KeyError
    ('no_collections', 'lookup', 'ansible.missing_collection.does_not_matter', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'ansible.builtin.invalid/name', AnsibleTemplateSyntaxError),  # plugin is None
    ('no_collections', 'lookup', 'ansible.builtin.invalid/name', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'ansible.builtin.missing_plugin', AnsibleTemplateSyntaxError),  # plugin is None
    ('no_collections', 'lookup', 'ansible.builtin.missing_plugin', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'ansible.builtin.quote', 'foo'),
    ('no_collections', 'lookup', 'ansible.builtin.env', []),
    ('no_collections', 'template', '{% if false %}{{ 123 | ansible.builtin.missing_plugin }}{% else %}Success{% endif %}', 'Success'),

    ('no_collections', 'filter', 'invalid/name', AnsibleTemplateSyntaxError),  # plugin is None
    ('no_collections', 'lookup', 'invalid/name', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'missing_plugin', AnsibleTemplateSyntaxError),  # plugin is None
    ('no_collections', 'lookup', 'missing_plugin', AnsibleTemplatePluginNotFoundError),
    ('no_collections', 'filter', 'quote', 'foo'),
    ('no_collections', 'lookup', 'env', []),
), ids=str)
def test_jinja2_loader_plugin(fixture: str, plugin_type: str, plugin_name: str, expected: t.Any) -> None:
    if plugin_type == 'filter':
        expression = f'{{{{ "foo" | {plugin_name} }}}}'
    elif plugin_type == 'template':
        expression = plugin_name  # abusing plugin_type and plugin_name to allow for testing arbitrary expressions
    else:
        expression = f'{{{{ lookup("{plugin_name}") }}}}'

    # HACK: this test should really be using a shared collection loader fixture, but this fixes an "inherited" dummy collection loader
    from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder

    try:
        _AnsibleCollectionFinder._remove()
        nuke_module_prefix('ansible_collections')
    except Exception:
        pass

    _AnsibleCollectionFinder(paths=[str(pathlib.Path(__file__).parent / 'fixtures' / fixture)])._install()

    try:
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                TemplateEngine().template(TRUST.tag(expression))
        else:
            assert TemplateEngine().template(TRUST.tag(expression)) == expected
    finally:
        _AnsibleCollectionFinder._remove()

        nuke_module_prefix('ansible_collections')


def test_variable_name_as_template_success() -> None:
    name = origin.tag("blar")

    res = TemplateEngine().variable_name_as_template(name)
    assert res.replace(' ', '') == "{{blar}}"

    required_tags: frozenset[AnsibleDatatagBase] = frozenset({origin, TrustedAsTemplate()})

    assert required_tags - AnsibleTagHelper.tags(res) == set()  # there might be others, that's fine


def test_variable_name_as_template_invalid() -> None:
    invalid_name = origin.tag("  invalid[var*name")

    with pytest.raises(AnsibleError) as err:
        TemplateEngine().variable_name_as_template(invalid_name)

    assert err.value.obj is invalid_name


@pytest.mark.parametrize("expression, expected", (
    ("dictthing.subdict1.subdict2", "hi mom"),
    ("dictthing.sublist1[0]", 1),
    ("dictthing[keys.sublist1][0]", 1),
    ("123", 123),
))
def test_resolve_variable_expression_success(expression: str, expected: t.Any) -> None:
    templar = TemplateEngine()

    local_variables = dict(
        dictthing=dict(sublist1=[1, 2, 3], subdict1=dict(subdict2="hi mom")),
        keys=dict(sublist1="sublist1")
    )

    assert templar.resolve_variable_expression(expression, local_variables=local_variables) == expected


@pytest.mark.parametrize("expression", (
    "'text'",
    "dictthing['subdict1']",
    "q('env')",
))
def test_resolve_variable_expression_invalid(expression: str) -> None:
    templar = TemplateEngine()

    with pytest.raises(AnsibleError) as err:
        templar.resolve_variable_expression(expression, local_variables=dict(dictthing=dict(subdict1=1)))

    assert err.value.obj is expression


def test_resolve_variable_expression_missing() -> None:
    templar = TemplateEngine()

    expr = origin.tag("missing_variable")

    with pytest.raises(AnsibleUndefinedVariable) as err:
        templar.resolve_variable_expression(expr)

    assert err.value.obj == expr  # may not be the same instance, since it was tagged TrustedAsTemplate internally

    required_tags: frozenset[AnsibleDatatagBase] = frozenset({origin, TrustedAsTemplate()})

    assert required_tags - AnsibleTagHelper.tags(err.value.obj) == set()  # there might be others, that's fine


def test_error_invalid_non_string_template():
    """Ensure errors on non-string template inputs include type information."""
    with pytest.raises(AnsibleTemplateError) as err:
        TemplateEngine().template(...)

    assert f"Type {type(...).__name__!r} is unsupported for variable storage." in err.value.message


def nuke_module_prefix(prefix):
    for module_to_nuke in [m for m in sys.modules if m.startswith(prefix)]:
        sys.modules.pop(module_to_nuke)


def test_template_transform_limit_exceeded(mocker: pytest_mock.MockerFixture) -> None:
    """
    Verify that template transforms cannot trigger an infinite loop.
    This currently requires injecting bogus transforms to trigger the condition, but the logic is present to catch future coding errors.
    """
    class One:
        def __init__(self, *args, **kwargs):
            pass

    class Two:
        def __init__(self, *args, **kwargs):
            pass

    mocker.patch.dict(_transform._type_transform_mapping, {One: Two, Two: One})

    with pytest.raises(AnsibleTemplateTransformLimitError):
        TemplateEngine(variables=dict(limit=One())).template(TRUST.tag("{{ limit }}"))


def test_transform_transform_limit_exceeded(mocker: pytest_mock.MockerFixture) -> None:
    """
    Verify that standalone recursive transforms cannot trigger an infinite loop.
    This currently requires injecting bogus transforms to trigger the condition, but the logic is present to catch future coding errors.
    """
    class One:
        def __init__(self, *args, **kwargs):
            pass

    class Two:
        def __init__(self, *args, **kwargs):
            pass

    mocker.patch.dict(_transform._type_transform_mapping, {One: Two, Two: One})

    with pytest.raises(AnsibleTemplateTransformLimitError):
        TemplateEngine().transform(One())


def test_deprecated_dedupe_and_source():
    """Validate dedupe and source context behavior for deprecated item access and associated warning behavior."""
    # unique tag instances that share the same contents (can be tracked independently by the audit context)
    deprecated_string = Deprecated(msg="deprecated").tag("deprecated string")
    deprecated_list = Deprecated(msg="deprecated").tag([42])
    deprecated_dict = Deprecated(msg="deprecated").tag(dict(key="value"))

    # a shared tag instance (cannot be tracked independently by the audit context)
    shared_tag_instance = Deprecated(msg="shared tag")
    d1 = shared_tag_instance.tag("d1")
    d2 = shared_tag_instance.tag("d2")

    variables = dict(
        indirect1=TRUST.tag('{{ indirect2 }}'),
        indirect2=TRUST.tag('{{ deprecated_string }}'),
        deprecated_string=deprecated_string,
        deprecated_list=deprecated_list,
        deprecated_dict=deprecated_dict,
        d1=d1,
        d2=d2,
        ansible_deprecation_warnings=True,
    )

    templar = TemplateEngine(variables=variables)

    with _display_utils.DeferredWarningContext(variables=variables) as dwc:
        # The indirect access summary occurs first.
        # The two following direct access summaries get deduped to a single one by the warning context (but unique template value keeps distinct from indirect).
        # The accesses with the shared tag instance values are internally deduped by the audit context.
        templar.evaluate_expression(TRUST.tag("indirect1 and deprecated_list and deprecated_dict and d1 and d2"))

    dep_warnings = dwc.get_deprecation_warnings()

    assert len(dep_warnings) == 3
    assert 'deprecated_string' in _event_utils.format_event_brief_message(dep_warnings[0].event)
    assert 'indirect1 and deprecated_list and deprecated_dict' in _event_utils.format_event_brief_message(dep_warnings[1].event)
    assert 'd1 and d2' in _event_utils.format_event_brief_message(dep_warnings[2].event)


def test_jinja_const_template_leak(template_context: TemplateContext) -> None:
    """Verify that _JinjaConstTemplate is present during internal templating."""
    with _display_utils.DeferredWarningContext(variables={}):  # suppress warning from usage of embedded template
        with unittest.mock.patch.object(_TemplateConfig, 'allow_embedded_templates', True):
            assert _JinjaConstTemplate.is_tagged_on(TemplateEngine().template(TRUST.tag("{{ '{{ 1 }}' }}")))


def test_jinja_const_template_finalized() -> None:
    """Verify that _JinjaConstTemplate is not present in finalized template results."""
    with _display_utils.DeferredWarningContext(variables={}):  # suppress warning from usage of embedded template
        with unittest.mock.patch.object(_TemplateConfig, 'allow_embedded_templates', True):
            assert not _JinjaConstTemplate.is_tagged_on(TemplateEngine().template(TRUST.tag("{{ '{{ 1 }}' }}")))


@pytest.mark.parametrize("template,expected", (
    ("{{ (-1).__abs__() }}", 1),
))
def test_unsafe_attr_access(template: str, expected: object) -> None:
    """Verify that unsafe attribute access fails by default and works when explicitly configured."""
    assert _TemplateConfig.sandbox_mode == _SandboxMode.DEFAULT

    with pytest.raises(AnsibleUndefinedVariable):
        TemplateEngine().template(TRUST.tag(template))

    with unittest.mock.patch.object(_TemplateConfig, 'sandbox_mode', _SandboxMode.ALLOW_UNSAFE_ATTRIBUTES):
        assert TemplateEngine().template(TRUST.tag(template)) == expected


def test_marker_from_test_plugin() -> None:
    """Verify test plugins can raise MarkerError to return a Marker, and that no warnings or deprecations are emitted."""
    with emits_warnings(deprecation_pattern=[], warning_pattern=[]):
        assert TemplateEngine(variables=dict(something=TRUST.tag("{{ nope }}"))).template(TRUST.tag("{{ (something is eq {}) is undefined }}"))


@pytest.mark.parametrize("template,expected", (
    ("{{ none }}", None),  # concat sees one node, NoneType result is preserved
    ("{% if False %}{% endif %}", None),  # concat sees one node, NoneType result is preserved
    ("{{''}}{% if False %}{% endif %}", ""),  # multiple blocks with an embedded None result, concat is in play, the result is an empty string
    ("hey {{ none }}", "hey "),  # composite template, the result is an empty string
    ("{% import 'importme' as imported %}{{ imported }}", "imported template result"),
))
def test_none_concat(template: str, expected: object) -> None:
    """Validate that None values are omitted from composite template concat."""
    te = TemplateEngine()

    # set up an importable template to exercise TemplateModule code paths
    te.environment.loader = DictLoader(dict(importme=TRUST.tag("{{ none }}{{ 'imported template result' }}{{ none }}")))

    assert te.template(TRUST.tag(template)) == expected


def test_filter_generator() -> None:
    """Verify that filters which return a generator are converted to a list while under the filter's JinjaCallContext."""
    variables = dict(
        foo=[
            dict(x=1, optional_var=0),
            dict(x=2),
        ],
        bar=TRUST.tag("{{ foo | selectattr('optional_var', 'defined') }}"),
    )

    te = TemplateEngine(variables=variables)
    te.template(TRUST.tag("{{ bar }}"))
    te.template(TRUST.tag("{{ lookup('vars', 'bar') }}"))


def test_call_context_reset() -> None:
    """Ensure that new template invocations do not inherit trip behavior from running Jinja plugins."""
    templar = TemplateEngine(variables=dict(
        somevar=TRUST.tag("{{ somedict.somekey | default('ok') }}"),
        somedict=dict(
            somekey=TRUST.tag("{{ not_here }}"),
        )
    ))

    assert templar.template(TRUST.tag("{{ lookup('vars', 'somevar') }}")) == 'ok'
