# -*- coding: utf-8 -*-

import unittest

import ansible.utils

class TestUtils(unittest.TestCase):

    #####################################
    ### varLookup function tests

    def test_varLookup_list(self):
        vars = {
            'data': {
                'who': ['joe', 'jack', 'jeff']
            }
        }

        res = ansible.utils.varLookup('${data.who}', vars)

        assert sorted(res) == sorted(vars['data']['who'])

    #####################################
    ### varReplace function tests

    def test_varReplace_simple(self):
        template = 'hello $who'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_multiple(self):
        template = '$what $who'
        vars = {
            'what': 'hello',
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_caps(self):
        template = 'hello $whoVar'
        vars = {
            'whoVar': 'world',
        }

        res = ansible.utils.varReplace(template, vars)
        print res
        assert res == 'hello world'

    def test_varReplace_middle(self):
        template = 'hello $who!'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world!'

    def test_varReplace_alternative(self):
        template = 'hello ${who}'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_almost_alternative(self):
        template = 'hello $who}'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world}'

    def test_varReplace_almost_alternative2(self):
        template = 'hello ${who'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == template

    def test_varReplace_alternative_greed(self):
        template = 'hello ${who} }'
        vars = {
            'who': 'world',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world }'

    def test_varReplace_notcomplex(self):
        template = 'hello $mydata.who'
        vars = {
            'data': {
                'who': 'world',
            },
        }

        res = ansible.utils.varReplace(template, vars)

        print res
        assert res == template

    def test_varReplace_nested(self):
        template = 'hello ${data.who}'
        vars = {
            'data': {
                'who': 'world'
            },
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_nested_int(self):
        template = '$what ${data.who}'
        vars = {
            'data': {
                'who': 2
            },
            'what': 'hello',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello 2'

    def test_varReplace_unicode(self):
        template = 'hello $who'
        vars = {
            'who': u'wórld',
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == u'hello wórld'

    def test_varReplace_list(self):
        template = 'hello ${data[1]}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_invalid_list(self):
        template = 'hello ${data[1}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == template

    def test_varReplace_list_oob(self):
        template = 'hello ${data[2]}'
        vars = {
            'data': [ 'no-one', 'world' ]
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == template

    def test_varReplace_list_nolist(self):
        template = 'hello ${data[1]}'
        vars = {
            'data': { 'no-one': 0, 'world': 1 }
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == template

    def test_varReplace_nested_list(self):
        template = 'hello ${data[1].msg[0]}'
        vars = {
            'data': [ 'no-one', {'msg': [ 'world'] } ]
        }

        res = ansible.utils.varReplace(template, vars)

        assert res == 'hello world'

    def test_varReplace_repr_basic(self):
        vars = {
            'color': '$favorite_color',
            'favorite_color': 'blue',
        }

        template = '$color == "blue"'
        res = ansible.utils.varReplace(template, vars, do_repr=True)
        assert eval(res)

    def test_varReplace_repr_varinvar(self):
        vars = {
            'foo': 'foo',
            'bar': 'bar',
            'foobar': '$foo$bar',
            'var': {
                'foo': 'foo',
                'foobar': '$foo$bar',
            },
        }

        template = '$foobar == "foobar"'
        res = ansible.utils.varReplace(template, vars, do_repr=True)
        assert eval(res)

    def test_varReplace_repr_varindex(self):
        vars = {
            'foo': 'foo',
            'var': {
                'foo': 'bar',
            },
        }

        template = '${var.$foo} == "bar"'
        res = ansible.utils.varReplace(template, vars, do_repr=True)
        assert eval(res)

    def test_varReplace_repr_varpartindex(self):
        vars = {
            'foo': 'foo',
            'var': {
                'foobar': 'foobar',
            },
        }

        template = '${var.${foo}bar} == "foobar"'
        res = ansible.utils.varReplace(template, vars, do_repr=True)
        assert eval(res)

    def test_varReplace_repr_nonstr(self):
        vars = {
            'foo': True,
            'bar': 1L,
        }

        template = '${foo} == $bar'
        res = ansible.utils.varReplace(template, vars, do_repr=True)
        assert res == 'True == 1L'

    def test_varReplace_consecutive_vars(self):
        vars = {
            'foo': 'foo',
            'bar': 'bar',
        }

        template = '${foo}${bar}'
        res = ansible.utils.varReplace(template, vars)
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
        res = ansible.utils.varReplace(template, vars)
        assert res == 'bar'

    def test_template_varReplace_iterated(self):
        template = 'hello $who'
        vars = {
            'who': 'oh great $person',
            'person': 'one',
        }

        res = ansible.utils.template(None, template, vars)

        assert res == u'hello oh great one'

    def test_varReplace_include(self):
        template = 'hello $FILE(world)'

        res = ansible.utils.template("test", template, {})

        assert res == u'hello world\n'

    def test_varReplace_include_script(self):
        template = 'hello $PIPE(echo world)'

        res = ansible.utils.template("test", template, {})

        assert res == u'hello world\n'

    #####################################
    ### Template function tests

    def test_template_basic(self):
        vars = {
            'who': 'world',
        }

        res = ansible.utils.template_from_file("test", "template-basic", vars)

        assert res == 'hello world'

    def test_template_whitespace(self):
        vars = {
            'who': 'world',
        }

        res = ansible.utils.template_from_file("test", "template-whitespace", vars)

        assert res == 'hello world\n'

    def test_template_unicode(self):
        vars = {
            'who': u'wórld',
        }

        res = ansible.utils.template_from_file("test", "template-basic", vars)

        assert res == u'hello wórld'

    #####################################
    ### key-value parsing

    def test_parse_kv_basic(self):
        assert (ansible.utils.parse_kv('a=simple b="with space" c="this=that"') ==
                {'a': 'simple', 'b': 'with space', 'c': 'this=that'})
