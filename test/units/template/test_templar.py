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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from jinja2.runtime import Context

from units.compat import unittest
from units.compat.mock import patch

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.template import Templar, AnsibleContext, AnsibleEnvironment, AnsibleUndefined
from ansible.utils.unsafe_proxy import AnsibleUnsafe, wrap_var
from units.mock.loader import DictDataLoader


class BaseTemplar(object):
    def setUp(self):
        self.test_vars = dict(
            foo="bar",
            bam="{{foo}}",
            num=1,
            var_true=True,
            var_false=False,
            var_dict=dict(a="b"),
            bad_dict="{a='b'",
            var_list=[1],
            recursive="{{recursive}}",
            some_var="blip",
            some_static_var="static_blip",
            some_keyword="{{ foo }}",
            some_unsafe_var=wrap_var("unsafe_blip"),
            some_static_unsafe_var=wrap_var("static_unsafe_blip"),
            some_unsafe_keyword=wrap_var("{{ foo }}"),
            str_with_error="{{ 'str' | from_json }}",
        )
        self.fake_loader = DictDataLoader({
            "/path/to/my_file.txt": "foo\n",
        })
        self.templar = Templar(loader=self.fake_loader, variables=self.test_vars)
        self._ansible_context = AnsibleContext(self.templar.environment, {}, {}, {})

    def is_unsafe(self, obj):
        return self._ansible_context._is_unsafe(obj)


# class used for testing arbitrary objects passed to template
class SomeClass(object):
    foo = 'bar'

    def __init__(self):
        self.blip = 'blip'


class SomeUnsafeClass(AnsibleUnsafe):
    def __init__(self):
        super(SomeUnsafeClass, self).__init__()
        self.blip = 'unsafe blip'


class TestTemplarTemplate(BaseTemplar, unittest.TestCase):
    def test_lookup_jinja_dict_key_in_static_vars(self):
        res = self.templar.template("{'some_static_var': '{{ some_var }}'}",
                                    static_vars=['some_static_var'])
        # self.assertEqual(res['{{ a_keyword }}'], "blip")
        print(res)

    def test_is_possibly_template_true(self):
        tests = [
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
        ]
        for test in tests:
            self.assertTrue(self.templar.is_possibly_template(test))

    def test_is_possibly_template_false(self):
        tests = [
            '{',
            '%',
            '#',
            'foo',
            '}}',
            '%}',
            'raw %}',
            '#}',
        ]
        for test in tests:
            self.assertFalse(self.templar.is_possibly_template(test))

    def test_is_possible_template(self):
        """This test ensures that a broken template still gets templated"""
        # Purposefully invalid jinja
        self.assertRaises(AnsibleError, self.templar.template, '{{ foo|default(False)) }}')

    def test_is_template_true(self):
        tests = [
            '{{ foo }}',
            '{% foo %}',
            '{# foo #}',
            '{# {{ foo }} #}',
            '{# {{ nothing }} {# #}',
            '{# {{ nothing }} {# #} #}',
            '{% raw %}{{ foo }}{% endraw %}',
        ]
        for test in tests:
            self.assertTrue(self.templar.is_template(test))

    def test_is_template_false(self):
        tests = [
            'foo',
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
        ]
        for test in tests:
            self.assertFalse(self.templar.is_template(test))

    def test_is_template_raw_string(self):
        res = self.templar.is_template('foo')
        self.assertFalse(res)

    def test_is_template_none(self):
        res = self.templar.is_template(None)
        self.assertFalse(res)

    def test_template_convert_bare_string(self):
        res = self.templar.template('foo', convert_bare=True)
        self.assertEqual(res, 'bar')

    def test_template_convert_bare_nested(self):
        res = self.templar.template('bam', convert_bare=True)
        self.assertEqual(res, 'bar')

    def test_template_convert_bare_unsafe(self):
        res = self.templar.template('some_unsafe_var', convert_bare=True)
        self.assertEqual(res, 'unsafe_blip')
        # self.assertIsInstance(res, AnsibleUnsafe)
        self.assertTrue(self.is_unsafe(res), 'returned value from template.template (%s) is not marked unsafe' % res)

    def test_template_convert_bare_filter(self):
        res = self.templar.template('bam|capitalize', convert_bare=True)
        self.assertEqual(res, 'Bar')

    def test_template_convert_bare_filter_unsafe(self):
        res = self.templar.template('some_unsafe_var|capitalize', convert_bare=True)
        self.assertEqual(res, 'Unsafe_blip')
        # self.assertIsInstance(res, AnsibleUnsafe)
        self.assertTrue(self.is_unsafe(res), 'returned value from template.template (%s) is not marked unsafe' % res)

    def test_template_convert_data(self):
        res = self.templar.template('{{foo}}', convert_data=True)
        self.assertTrue(res)
        self.assertEqual(res, 'bar')

    @patch('ansible.template.safe_eval', side_effect=AnsibleError)
    def test_template_convert_data_template_in_data(self, mock_safe_eval):
        res = self.templar.template('{{bam}}', convert_data=True)
        self.assertTrue(res)
        self.assertEqual(res, 'bar')

    def test_template_convert_data_bare(self):
        res = self.templar.template('bam', convert_data=True)
        self.assertTrue(res)
        self.assertEqual(res, 'bam')

    def test_template_convert_data_to_json(self):
        res = self.templar.template('{{bam|to_json}}', convert_data=True)
        self.assertTrue(res)
        self.assertEqual(res, '"bar"')

    def test_template_convert_data_convert_bare_data_bare(self):
        res = self.templar.template('bam', convert_data=True, convert_bare=True)
        self.assertTrue(res)
        self.assertEqual(res, 'bar')

    def test_template_unsafe_non_string(self):
        unsafe_obj = AnsibleUnsafe()
        res = self.templar.template(unsafe_obj)
        self.assertTrue(self.is_unsafe(res), 'returned value from template.template (%s) is not marked unsafe' % res)

    def test_template_unsafe_non_string_subclass(self):
        unsafe_obj = SomeUnsafeClass()
        res = self.templar.template(unsafe_obj)
        self.assertTrue(self.is_unsafe(res), 'returned value from template.template (%s) is not marked unsafe' % res)

    def test_weird(self):
        data = u'''1 2 #}huh{# %}ddfg{% }}dfdfg{{  {%what%} {{#foo#}} {%{bar}%} {#%blip%#} {{asdfsd%} 3 4 {{foo}} 5 6 7'''
        self.assertRaisesRegexp(AnsibleError,
                                'template error while templating string',
                                self.templar.template,
                                data)

    def test_template_with_error(self):
        """Check that AnsibleError is raised, fail if an unhandled exception is raised"""
        self.assertRaises(AnsibleError, self.templar.template, "{{ str_with_error }}")


class TestTemplarMisc(BaseTemplar, unittest.TestCase):
    def test_templar_simple(self):

        templar = self.templar
        # test some basic templating
        self.assertEqual(templar.template("{{foo}}"), "bar")
        self.assertEqual(templar.template("{{foo}}\n"), "bar\n")
        self.assertEqual(templar.template("{{foo}}\n", preserve_trailing_newlines=True), "bar\n")
        self.assertEqual(templar.template("{{foo}}\n", preserve_trailing_newlines=False), "bar")
        self.assertEqual(templar.template("{{bam}}"), "bar")
        self.assertEqual(templar.template("{{num}}"), 1)
        self.assertEqual(templar.template("{{var_true}}"), True)
        self.assertEqual(templar.template("{{var_false}}"), False)
        self.assertEqual(templar.template("{{var_dict}}"), dict(a="b"))
        self.assertEqual(templar.template("{{bad_dict}}"), "{a='b'")
        self.assertEqual(templar.template("{{var_list}}"), [1])
        self.assertEqual(templar.template(1, convert_bare=True), 1)

        # force errors
        self.assertRaises(AnsibleUndefinedVariable, templar.template, "{{bad_var}}")
        self.assertRaises(AnsibleUndefinedVariable, templar.template, "{{lookup('file', bad_var)}}")
        self.assertRaises(AnsibleError, templar.template, "{{lookup('bad_lookup')}}")
        self.assertRaises(AnsibleError, templar.template, "{{recursive}}")
        self.assertRaises(AnsibleUndefinedVariable, templar.template, "{{foo-bar}}")

        # test with fail_on_undefined=False
        self.assertEqual(templar.template("{{bad_var}}", fail_on_undefined=False), "{{bad_var}}")

        # test setting available_variables
        templar.available_variables = dict(foo="bam")
        self.assertEqual(templar.template("{{foo}}"), "bam")
        # variables must be a dict() for available_variables setter
        # FIXME Use assertRaises() as a context manager (added in 2.7) once we do not run tests on Python 2.6 anymore.
        try:
            templar.available_variables = "foo=bam"
        except AssertionError:
            pass
        except Exception as e:
            self.fail(e)

    def test_templar_escape_backslashes(self):
        # Rule of thumb: If escape backslashes is True you should end up with
        # the same number of backslashes as when you started.
        self.assertEqual(self.templar.template("\t{{foo}}", escape_backslashes=True), "\tbar")
        self.assertEqual(self.templar.template("\t{{foo}}", escape_backslashes=False), "\tbar")
        self.assertEqual(self.templar.template("\\{{foo}}", escape_backslashes=True), "\\bar")
        self.assertEqual(self.templar.template("\\{{foo}}", escape_backslashes=False), "\\bar")
        self.assertEqual(self.templar.template("\\{{foo + '\t' }}", escape_backslashes=True), "\\bar\t")
        self.assertEqual(self.templar.template("\\{{foo + '\t' }}", escape_backslashes=False), "\\bar\t")
        self.assertEqual(self.templar.template("\\{{foo + '\\t' }}", escape_backslashes=True), "\\bar\\t")
        self.assertEqual(self.templar.template("\\{{foo + '\\t' }}", escape_backslashes=False), "\\bar\t")
        self.assertEqual(self.templar.template("\\{{foo + '\\\\t' }}", escape_backslashes=True), "\\bar\\\\t")
        self.assertEqual(self.templar.template("\\{{foo + '\\\\t' }}", escape_backslashes=False), "\\bar\\t")

    def test_template_jinja2_extensions(self):
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)

        old_exts = C.DEFAULT_JINJA2_EXTENSIONS
        try:
            C.DEFAULT_JINJA2_EXTENSIONS = "foo,bar"
            self.assertEqual(templar._get_extensions(), ['foo', 'bar'])
        finally:
            C.DEFAULT_JINJA2_EXTENSIONS = old_exts


class TestTemplarLookup(BaseTemplar, unittest.TestCase):
    def test_lookup_missing_plugin(self):
        self.assertRaisesRegexp(AnsibleError,
                                r'lookup plugin \(not_a_real_lookup_plugin\) not found',
                                self.templar._lookup,
                                'not_a_real_lookup_plugin',
                                'an_arg', a_keyword_arg='a_keyword_arg_value')

    def test_lookup_list(self):
        res = self.templar._lookup('list', 'an_arg', 'another_arg')
        self.assertEqual(res, 'an_arg,another_arg')

    def test_lookup_jinja_undefined(self):
        self.assertRaisesRegexp(AnsibleUndefinedVariable,
                                "'an_undefined_jinja_var' is undefined",
                                self.templar._lookup,
                                'list', '{{ an_undefined_jinja_var }}')

    def test_lookup_jinja_defined(self):
        res = self.templar._lookup('list', '{{ some_var }}')
        self.assertTrue(self.is_unsafe(res))
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_dict_string_passed(self):
        self.assertRaisesRegexp(AnsibleError,
                                "with_dict expects a dict",
                                self.templar._lookup,
                                'dict',
                                '{{ some_var }}')

    def test_lookup_jinja_dict_list_passed(self):
        self.assertRaisesRegexp(AnsibleError,
                                "with_dict expects a dict",
                                self.templar._lookup,
                                'dict',
                                ['foo', 'bar'])

    def test_lookup_jinja_kwargs(self):
        res = self.templar._lookup('list', 'blip', random_keyword='12345')
        self.assertTrue(self.is_unsafe(res))
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_list_wantlist(self):
        res = self.templar._lookup('list', '{{ some_var }}', wantlist=True)
        self.assertEqual(res, ["blip"])

    def test_lookup_jinja_list_wantlist_undefined(self):
        self.assertRaisesRegexp(AnsibleUndefinedVariable,
                                "'some_undefined_var' is undefined",
                                self.templar._lookup,
                                'list',
                                '{{ some_undefined_var }}',
                                wantlist=True)

    def test_lookup_jinja_list_wantlist_unsafe(self):
        res = self.templar._lookup('list', '{{ some_unsafe_var }}', wantlist=True)
        for lookup_result in res:
            self.assertTrue(self.is_unsafe(lookup_result))
            # self.assertIsInstance(lookup_result, AnsibleUnsafe)

        # Should this be an AnsibleUnsafe
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_dict(self):
        res = self.templar._lookup('list', {'{{ a_keyword }}': '{{ some_var }}'})
        self.assertEqual(res['{{ a_keyword }}'], "blip")
        # TODO: Should this be an AnsibleUnsafe
        # self.assertIsInstance(res['{{ a_keyword }}'], AnsibleUnsafe)
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_dict_unsafe(self):
        res = self.templar._lookup('list', {'{{ some_unsafe_key }}': '{{ some_unsafe_var }}'})
        self.assertTrue(self.is_unsafe(res['{{ some_unsafe_key }}']))
        # self.assertIsInstance(res['{{ some_unsafe_key }}'], AnsibleUnsafe)
        # TODO: Should this be an AnsibleUnsafe
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_dict_unsafe_value(self):
        res = self.templar._lookup('list', {'{{ a_keyword }}': '{{ some_unsafe_var }}'})
        self.assertTrue(self.is_unsafe(res['{{ a_keyword }}']))
        # self.assertIsInstance(res['{{ a_keyword }}'], AnsibleUnsafe)
        # TODO: Should this be an AnsibleUnsafe
        # self.assertIsInstance(res, AnsibleUnsafe)

    def test_lookup_jinja_none(self):
        res = self.templar._lookup('list', None)
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
        context = self._context(variables={'some_unsafe_key': wrap_var('some_unsafe_string')})
        res = context.resolve('some_unsafe_key')
        # self.assertIsInstance(res, AnsibleUnsafe)
        self.assertTrue(self.is_unsafe(res),
                        'return of AnsibleContext.resolve (%s) was expected to be marked unsafe but was not' % res)

    def test_resolve_unsafe_list(self):
        context = self._context(variables={'some_unsafe_key': [wrap_var('some unsafe string 1')]})
        res = context.resolve('some_unsafe_key')
        # self.assertIsInstance(res[0], AnsibleUnsafe)
        self.assertTrue(self.is_unsafe(res),
                        'return of AnsibleContext.resolve (%s) was expected to be marked unsafe but was not' % res)

    def test_resolve_unsafe_dict(self):
        context = self._context(variables={'some_unsafe_key':
                                           {'an_unsafe_dict': wrap_var('some unsafe string 1')}
                                           })
        res = context.resolve('some_unsafe_key')
        self.assertTrue(self.is_unsafe(res['an_unsafe_dict']),
                        'return of AnsibleContext.resolve (%s) was expected to be marked unsafe but was not' % res['an_unsafe_dict'])

    def test_resolve(self):
        context = self._context(variables={'some_key': 'some_string'})
        res = context.resolve('some_key')
        self.assertEqual(res, 'some_string')
        # self.assertNotIsInstance(res, AnsibleUnsafe)
        self.assertFalse(self.is_unsafe(res),
                         'return of AnsibleContext.resolve (%s) was not expected to be marked unsafe but was' % res)

    def test_resolve_none(self):
        context = self._context(variables={'some_key': None})
        res = context.resolve('some_key')
        self.assertEqual(res, None)
        # self.assertNotIsInstance(res, AnsibleUnsafe)
        self.assertFalse(self.is_unsafe(res),
                         'return of AnsibleContext.resolve (%s) was not expected to be marked unsafe but was' % res)

    def test_is_unsafe(self):
        context = self._context()
        self.assertFalse(context._is_unsafe(AnsibleUndefined()))
