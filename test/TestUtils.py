# -*- coding: utf-8 -*-

import unittest
import os
import os.path
import tempfile

from nose.plugins.skip import SkipTest

import ansible.utils
import ansible.utils.template as template2

class TestUtils(unittest.TestCase):

    #####################################
    ### varReplace function tests

    def test_varReplace_simple(self):
        template = 'hello $who'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_trailing_dollar(self):
        template = '$what $who $'
        vars = dict(what='hello', who='world')
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'hello world $'

    def test_varReplace_multiple(self):
        template = '$what $who'
        vars = {
            'what': 'hello',
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_caps(self):
        template = 'hello $whoVar'
        vars = {
            'whoVar': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)
        print res
        assert res == 'hello world'

    def test_varReplace_middle(self):
        template = 'hello $who!'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world!'

    def test_varReplace_alternative(self):
        template = 'hello ${who}'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_almost_alternative(self):
        template = 'hello $who}'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world}'

    def test_varReplace_almost_alternative2(self):
        template = 'hello ${who'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == template

    def test_varReplace_alternative_greed(self):
        template = 'hello ${who} }'
        vars = {
            'who': 'world',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world }'

    def test_varReplace_notcomplex(self):
        template = 'hello $mydata.who'
        vars = {
            'data': {
                'who': 'world',
            },
        }

        res = template2.legacy_varReplace(None, template, vars)

        print res
        assert res == template

    def test_varReplace_nested(self):
        template = 'hello ${data.who}'
        vars = {
            'data': {
                'who': 'world'
            },
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_nested_int(self):
        template = '$what ${data.who}'
        vars = {
            'data': {
                'who': 2
            },
            'what': 'hello',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello 2'

    def test_varReplace_unicode(self):
        template = 'hello $who'
        vars = {
            'who': u'wórld',
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == u'hello wórld'

    def test_varReplace_list(self):
        template = 'hello ${data[1]}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_invalid_list(self):
        template = 'hello ${data[1}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == template

    def test_varReplace_list_oob(self):
        template = 'hello ${data[2]}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == template

    def test_varReplace_list_nolist(self):
        template = 'hello ${data[1]}'
        vars = {
            'data': { 'no-one': 0, 'world': 1 }
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == template

    def test_varReplace_nested_list(self):
        template = 'hello ${data[1].msg[0]}'
        vars = {
            'data': [ 'no-one', {'msg': [ 'world'] } ]
        }

        res = template2.legacy_varReplace(None, template, vars)

        assert res == 'hello world'

    def test_varReplace_consecutive_vars(self):
        vars = {
            'foo': 'foo',
            'bar': 'bar',
        }

        template = '${foo}${bar}'
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'foobar'

    def test_varReplace_escape_dot(self):
        vars = {
            'hostvars': {
                'test.example.com': {
                    'foo': 'bar',
                },
            },
        }

        template = '${hostvars.{test.example.com}.foo}'
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'bar'

    def test_varReplace_list_join(self):
        vars = {
            'list': [
                'foo',
                'bar',
                'baz',
            ],
        }

        template = 'yum pkg=${list} state=installed'
        res = template2.legacy_varReplace(None, template, vars, expand_lists=True)
        assert res == 'yum pkg=foo,bar,baz state=installed'

    def test_varReplace_escaped_var(self):
        vars = {
            'foo': 'bar',
        }
        template = 'action \$foo'
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'action $foo'

    def test_varReplace_var_part(self):
        vars = {
            'foo': {
                'bar': 'result',
            },
            'key': 'bar',
        }
        template = 'test ${foo.$key}'
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'test result'

    def test_varReplace_var_partial_part(self):
        vars = {
            'foo': {
                'barbaz': 'result',
            },
            'key': 'bar',
        }
        template = 'test ${foo.${key}baz}'
        res = template2.legacy_varReplace(None, template, vars)
        assert res == 'test result'

    def test_varReplace_var_complex_var(self):
        vars = {
            'x': '$y',
            'y': {
                'foo': 'result',
            },
        }
        template = '${x.foo}'
        res = template2.template(None, template, vars)
        assert res == 'result'

    def test_template_varReplace_iterated(self):
        template = 'hello $who'
        vars = {
            'who': 'oh great $person',
            'person': 'one',
        }

        res = template2.template(None, template, vars)

        assert res == u'hello oh great one'

    def test_varReplace_include(self):
        template = 'hello $FILE(world) $LOOKUP(file, $filename)'

        res = template2.template("test", template, {'filename': 'world'}, expand_lists=True)

        assert res == u'hello world world'

    def test_varReplace_include_script(self):
        template = 'hello $PIPE(echo world) $LOOKUP(pipe, echo world)'

        res = template2.template("test", template, {}, expand_lists=True)

        assert res == u'hello world world'

    #####################################
    ### template_ds function tests

    def test_template_ds_basic(self):
        vars = {
            'data': {
                'var': [
                    'foo',
                    'bar',
                    'baz',
                ],
                'types': [
                    'str',
                    u'unicode',
                    1,
                    1L,
                    1.2,
                ],
                'alphas': '$alphas',
            },
            'alphas': [
                'abc',
                'def',
                'ghi',
            ],
        }

        template = '${data.var}'
        res = template2.template(None, template, vars)
        assert sorted(res) == sorted(vars['data']['var'])

        template = '${data.types}'
        res = template2.template(None, template, vars)
        assert sorted(res) == sorted(vars['data']['types'])

        template = '${data.alphas}'
        res = template2.template(None, template, vars)
        assert sorted(res) == sorted(vars['alphas'])

        template = '${data.nonexisting}'
        res = template2.template(None, template, vars)
        assert res == template

    #####################################
    ### Template function tests

    def test_template_basic(self):
        vars = {
            'who': 'world',
        }

        res = template2.template_from_file("test", "template-basic", vars)

        assert res == 'hello world'

    def test_template_whitespace(self):
        vars = {
            'who': 'world',
        }

        res = template2.template_from_file("test", "template-whitespace", vars)

        assert res == 'hello world\n'

    def test_template_unicode(self):
        vars = {
            'who': u'wórld',
        }

        res = template2.template_from_file("test", "template-basic", vars)

        assert res == u'hello wórld'


    #####################################
    ### check_conditional tests

    def test_check_conditional_jinja2_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # boolean
        assert(ansible.utils.check_conditional(
            'jinja2_compare true', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare false', '/', {}) == False)
        assert(ansible.utils.check_conditional(
            'jinja2_compare True', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare False', '/', {}) == False)

        # integer
        assert(ansible.utils.check_conditional(
            'jinja2_compare 1', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare 0', '/', {}) == False)

        # string, beware, a string is truthy unless empty
        assert(ansible.utils.check_conditional(
            'jinja2_compare "yes"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare "no"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare ""', '/', {}) == False)


    def test_check_conditional_jinja2_variable_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # boolean
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'True'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'true'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'False'}) == False)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'false'}) == False)

        # integer
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '1'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 1}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '0'}) == False)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 0}) == False)

        # string, beware, a string is truthy unless empty
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '"yes"'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '"no"'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '""'}) == False)

        # Python boolean in Jinja2 expression
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': True}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': False}) == False)


    def test_check_conditional_jinja2_expression(self):
        assert(ansible.utils.check_conditional(
            'jinja2_compare 1 == 1', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare bar == 42', '/', {'bar': 42}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare bar != 42', '/', {'bar': 42}) == False)


    def test_check_conditional_jinja2_expression_in_variable(self):
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': '1 == 1'}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'bar == 42', 'bar': 42}) == True)
        assert(ansible.utils.check_conditional(
            'jinja2_compare var', '/', {'var': 'bar != 42', 'bar': 42}) == False)

    def test_check_conditional_jinja2_unicode(self):
        assert(ansible.utils.check_conditional(
            u'jinja2_compare "\u00df"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            u'jinja2_compare var == "\u00df"', '/', {'var': u'\u00df'}) == True)


    #####################################
    ### key-value parsing

    def test_parse_kv_basic(self):
        assert (ansible.utils.parse_kv('a=simple b="with space" c="this=that"') ==
                {'a': 'simple', 'b': 'with space', 'c': 'this=that'})

    #####################################
    ### plugins

    def test_loaders_expanduser_each_dir(self):
        # Test that PluginLoader will call expanduser on each path
        # when it splits its "config" argument.
        home_dir = os.path.expanduser("~")
        if home_dir == "~":
            raise SkipTest("your platform doesn't expand ~ in paths")
        elif not os.path.isdir(home_dir):
            raise SkipTest("~ expands to non-directory %r" % (home_dir,))
        elif not os.path.isabs(home_dir):
            raise SkipTest("~ expands to non-absolute path %r" % (home_dir,))
        # Unfortunately we have to create temporary directories in
        # your home directory; the directories have to exist for
        # PluginLoader to accept them.
        abs_dirs, tilde_dirs = [], []
        try:
            for _ in range(2):
                temp_dir = tempfile.mkdtemp(prefix="ansible", dir=home_dir)
                abs_dirs.append(temp_dir)
                # Convert mkdtemp's absolute path to one starting with "~".
                tilde_dir = os.path.join("~", os.path.relpath(temp_dir,
                                                              home_dir))
                tilde_dirs.append(tilde_dir)
            loader = ansible.utils.plugins.PluginLoader(
                "",
                "",
                os.pathsep.join(tilde_dirs),
                "something_under_basedir"
            )
            loader_paths = loader.print_paths().split(os.pathsep)
            for abs_dir in abs_dirs:
                assert abs_dir in loader_paths, \
                    "%r not in %r" % (abs_dir, loader_paths)
        finally:
            for a_dir in abs_dirs:
                try:
                    os.rmdir(a_dir)
                except os.error:
                    pass
