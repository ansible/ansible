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

import sys
from collections import defaultdict

from ansible.compat.tests import unittest
from ansible.vars.unsafe_proxy import wrap_var, AnsibleUnsafeText
from ansible.compat.six import string_types

from ansible.template.safe_eval import safe_eval


class BaseSafeEval(object):
    _debug = False

    def setUp(self):
        self._locals = {}

    def _eval(self, code, expected, expected_type,
              locals=None, expected_exc_type=None, expected_exc_message=None):
        _locals = locals or self._locals
        # adding the include_exceptions=True changes the type returned...
        res = safe_eval(code, locals=_locals)
        if self._debug:
            print('code: %s' % code)
            print('expected: %s' % expected)
            print('res: %s' % res)
            print('expected_type: %s' % expected_type)
            print('type: %s' % type(res))
            print('_locals: %s' % locals)
            print('repr(res): %s' % repr(res))
            if hasattr(res, 'inst_attr'):
                print('inst_attr: %s' % res.inst_attr)
        self.assertIsInstance(res, expected_type)
        self.assertEquals(res, expected)
        self._res = res
        return res


class TestSafeEval(BaseSafeEval, unittest.TestCase):
    # test safe eval calls with different possible types for the
    # locals dictionary, to ensure we don't run into problems like
    # ansible/ansible/issues/12206 again

    def test_empty_string(self):
        self._eval('', '', string_types, self._locals)

    def test_string(self):
        self._eval('foo', 'foo', string_types, self._locals)

    def test_quoted_string(self):
        code = '''"foo"'''
        self._eval(code, 'foo', string_types, self._locals)

    def test_escaped_quoted_string(self):
        code = '''\"foo\"'''
        self._eval(code, 'foo', string_types, self._locals)

    def test_double_escaped_quoted_string(self):
        code = '''\\"foo\\"'''
        self._eval(code, code, string_types, self._locals)

    def test_int_literal(self):
        self._eval('1', 1, int, self._locals)

    def test_float_literal(self):
        self._eval('37.1', 37.1, float, self._locals)

    def test_bool_true(self):
        self._eval('True', True, bool, self._locals)

    def test_bool_false(self):
        self._eval('False', False, bool, self._locals)

    def test_json_bool_true(self):
        self._eval('true', True, bool, self._locals)

    def test_json_bool_false(self):
        self._eval('false', False, bool, self._locals)

    def test_none(self):
        self._eval('None', None, type(None), self._locals)

    def test_json_null(self):
        self._eval('null', None, type(None), self._locals)

    def test_list_empty(self):
        self._eval('[]', [], list, self._locals)

    def test_dict_empty(self):
        self._eval('{}', {}, dict, self._locals)

    def test_dict_keyword_empty(self):
        self._eval('dict()', 'dict()', string_types, self._locals, Exception,
                   expected_exc_message='invalid function: dict')

    def test_dict_string(self):
        code = '''{"key_string": "value_string"}'''
        self._eval(code, {'key_string': 'value_string'}, dict, self._locals)

    def test_tuple_empty(self):
        self._eval('()', (), tuple, self._locals)

    def test_tuple_strings(self):
        self._eval('("foo", "blip")', ("foo", "blip"), tuple, self._locals)

#    def test_named_tuple(self):
#        from collections import namedtuple
#        self._eval('namedtuple("Blip", ["a","b"])', namedtuple("Blip", ["a", "b"]), namedtuple, self._locals)

    def test_lambda(self):
        code = '''lambda a, b: a+b'''
        self._eval(code, code, string_types, self._locals, Exception,
                   expected_exc_message='invalid expression (lambda a, b: a+b)')

    def test_if(self):
        code = '''if True: pass'''
        self._eval(code, code, string_types, self._locals)

    def test_eval(self):
        code = '''eval()'''
        self._eval(code, code, string_types, self._locals, Exception,
                   expected_exc_message='invalid function: eval')

    def test_filter_asdfasdf(self):
        code = '''asdfasdf'''
        self._eval(code, code, string_types, self._locals, NameError,
                   expected_exc_message="name 'asdfasdf' is not defined")

    def test_non_string(self):
        code = ['whatever']
        self._eval(code, code, list, self._locals)

    def test_builtin_method_zip(self):
        code = '''zip()'''
        self._eval(code, code, string_types, self._locals, Exception,
                   expected_exc_message='invalid function: zip')

    def test_call_some_obj(self):
        code = '''some_obj()'''
        _locals = {'some_obj': set(['foo'])}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_list_comprehension(self):
        code = '''[x for x in some_list]'''
        _locals = {'some_list': [1, 2, 'c', 'Dee', 2.1718]}
        self._eval(code, code, string_types, _locals, Exception,
                   expected_exc_message='invalid expression ([x for x in some_list])')

    @unittest.skipUnless(sys.version_info[:2] >= (2, 7), "Python 2.6 has no set literals")
    def test_set(self):
        code = '''{1,2,3}'''
        self._eval(code, {1, 2, 3}, set, self._locals)

    def test_yield(self):
        code = '''yield some_item'''
        _locals = {'some_item': [1, 2]}
        self._eval(code, code, string_types, _locals)

    def test_subscript(self):
        code = '''foo[1:2]'''
        _locals = {'foo': ['a', 'b', 'c', 'd']}
        self._eval(code, code, string_types, _locals, Exception,
                   expected_exc_message='invalid expression (foo[1:2])')

    def test_call(self):
        code = '''some_method(blip, 1)'''

        def some_method(arg1, arg2):
            return arg1 + arg2
        # adding some_method to passed in locals, otherwise
        # 'in builtin and not in whitelist' filters it or it is not found
        _locals = {'some_method': some_method,
                   'blip': 2}
        # Note this calls the method and returns the result
        self._eval(code, 3, int, _locals)

    def test_call_getattr(self):
        code = '''getattr(builtins, "locals")'''
        # gettatr is in builtins but not in the callable whitelist
        self._eval(code, code, string_types, self._locals, Exception,
                   expected_exc_message='invalid function: getattr')

    @unittest.skipUnless(sys.version_info[:2] >= (2, 7), "Python 2.6 has no set literals")
    def test_set_literals(self):
        self.assertEqual(safe_eval('{0}'), set([0]))


class SomeClass():
    some_class_attr = 1

    def __init__(self, inst_attr=None):
        self.inst_attr = inst_attr or "some_inst_attr"


class SomeClassWithRepr():
    def __init__(self, inst_attr=None):
        self.inst_attr = inst_attr or "some_inst_attr (with_repr)"

    def __repr__(self):
        return """'type(some_obj)("some arg in the eval")'"""


# TODO: once this is sorted, added it back to TestSafeEval so it gets tested under the other permutations
#       It is split to it's own class for now just to reduce noise.
class TestSafeEvalType(BaseSafeEval, unittest.TestCase):
    def setUp(self):
        self._locals = {}
        self._debug = False

    def test_builtin_method_type(self):
        code = '''type(type)'''
        self._eval(code, code, string_types, self._locals, TypeError)

    def test_builtin_method_type_call(self):
        code = '''type(type)()'''
        self._eval(code, code, string_types, self._locals, TypeError)

    def test_builtin_method_type_some_obj(self):
        code = '''type(some_obj)'''
        _locals = {'some_obj': set(['foo'])}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call(self):
        code = '''type(some_obj)()'''
        _locals = {'some_obj': set(['foo'])}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_unicode_call(self):
        code = '''type(some_obj)("http://badplace")'''
        url = "https://goodplace"
        _locals = {'some_obj': url}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_unicode_call_set_value(self):
        code = '''some_obj="http://badplace"'''
        url = "https://goodplace"
        _locals = {'some_obj': url}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_unsafe_var(self):
        unsafe_var = wrap_var('''type(some_safe_var)("blippy is bad")''')
        unsafe_var_a = AnsibleUnsafeText('''type(some_safe_var)("blippy is bad")''')
        safe_var = '''whatever this is ok'''

        _locals = {'some_unsafe_var': unsafe_var_a,
                   'some_safe_var': safe_var}
        self._eval(unsafe_var, unsafe_var, string_types, _locals, TypeError)
        self.assertTrue(hasattr(self._res, '__UNSAFE__'))

    def test_builtin_method_type_some_obj_call_dict(self):
        code = u'''type(some_obj)()'''
        _locals = {'some_obj': {'some_key': 'some_value'}}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call_with_args(self):
        code = '''type(some_obj)(1, 2, "some_string")'''
        _locals = {'some_obj': set(['foo'])}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_local_class(self):
        code = '''type(some_obj)'''
        _locals = {'some_obj': SomeClass()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_local_class_recurse(self):
        code = '''type(type(some_obj).bli)()'''
        _locals = {'some_obj': SomeClass()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call_local_class(self):
        code = '''type(some_obj)()'''
        _locals = {'some_obj': SomeClass()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call_local_class_with_args(self):
        code = '''type(some_obj)("some arg in the eval")'''
        _locals = {'some_obj': SomeClass()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_local_class_repr(self):
        code = '''type(some_obj)'''
        _locals = {'some_obj': SomeClassWithRepr()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call_local_class_repr(self):
        code = '''type(some_obj)()'''
        _locals = {'some_obj': SomeClassWithRepr()}
        self._eval(code, code, string_types, _locals, TypeError)

    def test_builtin_method_type_some_obj_call_local_class_with_args_repr(self):
        code = '''type(some_obj)("some arg in the eval")'''
        _locals = {'some_obj': SomeClassWithRepr()}
        self._eval(code, code, string_types, _locals, TypeError)


class TestSafeEvalDefaultDict(TestSafeEval):
    def setUp(self):
        self._locals = defaultdict(dict)


class TestSafeEvalIncludeExceptions(TestSafeEval):
    def _eval(self, code, expected, expected_type,
              locals=None, expected_exc_type=None, expected_exc_message=None):
        _locals = locals or self._locals

        # adding the include_exceptions=True changes the type returned...
        res, exc = safe_eval(code, locals=_locals, include_exceptions=True)

        self.assertEquals(res, expected)
        self.assertIsInstance(res, expected_type)
        if expected_exc_type:
            self.assertIsInstance(exc, expected_exc_type)
        if expected_exc_message:
            self.assertEquals(exc.message, expected_exc_message)
        return res


class TestSafeEvalIncludeExceptionsDefaultDict(TestSafeEvalIncludeExceptions):
    def setUp(self):
        self._locals = defaultdict(dict)
