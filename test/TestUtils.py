# -*- coding: utf-8 -*-

import unittest

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
    ### key-value parsing

    def test_parse_kv_basic(self):
        assert (ansible.utils.parse_kv('a=simple b="with space" c="this=that"') ==
                {'a': 'simple', 'b': 'with space', 'c': 'this=that'})
