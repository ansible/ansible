# -*- coding: utf-8 -*-

import unittest
import os
import os.path
import tempfile

from nose.plugins.skip import SkipTest

import ansible.utils
import ansible.utils.template as template2

import sys
reload(sys)
sys.setdefaultencoding("utf8") 

class TestUtils(unittest.TestCase):

    #####################################
    ### varReplace function tests

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
