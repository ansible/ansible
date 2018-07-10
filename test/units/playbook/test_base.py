# (c) 2016, Adrian Likins <alikins@redhat.com>
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

from ansible.compat.tests import unittest

from ansible.errors import AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar
from ansible.playbook import base

from units.mock.loader import DictDataLoader


class TestBase(unittest.TestCase):
    ClassUnderTest = base.Base

    def setUp(self):
        self.assorted_vars = {'var_2_key': 'var_2_value',
                              'var_1_key': 'var_1_value',
                              'a_list': ['a_list_1', 'a_list_2'],
                              'a_dict': {'a_dict_key': 'a_dict_value'},
                              'a_set': set(['set_1', 'set_2']),
                              'a_int': 42,
                              'a_float': 37.371,
                              'a_bool': True,
                              'a_none': None,
                              }
        self.b = self.ClassUnderTest()

    def _base_validate(self, ds):
        bsc = self.ClassUnderTest()
        parent = ExampleParentBaseSubClass()
        bsc._parent = parent
        bsc._dep_chain = [parent]
        parent._dep_chain = None
        bsc.load_data(ds)
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        bsc.post_validate(templar)
        return bsc

    def test(self):
        self.assertIsInstance(self.b, base.Base)
        self.assertIsInstance(self.b, self.ClassUnderTest)

    # dump me doesnt return anything or change anything so not much to assert
    def test_dump_me_empty(self):
        self.b.dump_me()

    def test_dump_me(self):
        ds = {'environment': [],
              'vars': {'var_2_key': 'var_2_value',
                       'var_1_key': 'var_1_value'}}
        b = self._base_validate(ds)
        b.dump_me()

    def _assert_copy(self, orig, copy):
        self.assertIsInstance(copy, self.ClassUnderTest)
        self.assertIsInstance(copy, base.Base)
        self.assertEquals(len(orig._valid_attrs),
                          len(copy._valid_attrs))

        sentinel = 'Empty DS'
        self.assertEquals(getattr(orig, '_ds', sentinel),
                          getattr(copy, '_ds', sentinel))

    def test_copy_empty(self):
        copy = self.b.copy()
        self._assert_copy(self.b, copy)

    def test_copy_with_vars(self):
        ds = {'vars': self.assorted_vars}
        b = self._base_validate(ds)

        copy = b.copy()
        self._assert_copy(b, copy)

    def test_serialize(self):
        ds = {}
        ds = {'environment': [],
              'vars': self.assorted_vars
              }
        b = self._base_validate(ds)
        ret = b.serialize()
        self.assertIsInstance(ret, dict)

    def test_deserialize(self):
        data = {}

        d = self.ClassUnderTest()
        d.deserialize(data)
        self.assertIn('run_once', d._attributes)
        self.assertIn('check_mode', d._attributes)

        data = {'no_log': False,
                'remote_user': None,
                'vars': self.assorted_vars,
                'environment': [],
                'run_once': False,
                'connection': None,
                'ignore_errors': False,
                'port': 22,
                'a_sentinel_with_an_unlikely_name': ['sure, a list']}

        d = self.ClassUnderTest()
        d.deserialize(data)
        self.assertNotIn('a_sentinel_with_an_unlikely_name', d._attributes)
        self.assertIn('run_once', d._attributes)
        self.assertIn('check_mode', d._attributes)

    def test_serialize_then_deserialize(self):
        ds = {'environment': [],
              'vars': self.assorted_vars}
        b = self._base_validate(ds)
        copy = b.copy()
        ret = b.serialize()
        b.deserialize(ret)
        c = self.ClassUnderTest()
        c.deserialize(ret)
        # TODO: not a great test, but coverage...
        self.maxDiff = None
        self.assertDictEqual(b.serialize(), copy.serialize())
        self.assertDictEqual(c.serialize(), copy.serialize())

    def test_post_validate_empty(self):
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        ret = self.b.post_validate(templar)
        self.assertIsNone(ret)

    def test_get_ds_none(self):
        ds = self.b.get_ds()
        self.assertIsNone(ds)

    def test_load_data_ds_is_none(self):
        self.assertRaises(AssertionError, self.b.load_data, None)

    def test_load_data_invalid_attr(self):
        ds = {'not_a_valid_attr': [],
              'other': None}

        self.assertRaises(AnsibleParserError, self.b.load_data, ds)

    def test_load_data_invalid_attr_type(self):
        ds = {'environment': True}

        # environment is supposed to be  a list. This
        # seems like it shouldn't work?
        ret = self.b.load_data(ds)
        self.assertEquals(True, ret._attributes['environment'])

    def test_post_validate(self):
        ds = {'environment': [],
              'port': 443}
        b = self._base_validate(ds)
        self.assertEquals(b.port, 443)
        self.assertEquals(b.environment, [])

    def test_post_validate_invalid_attr_types(self):
        ds = {'environment': [],
              'port': 'some_port'}
        b = self._base_validate(ds)
        self.assertEquals(b.port, 'some_port')

    def test_squash(self):
        data = self.b.serialize()
        self.b.squash()
        squashed_data = self.b.serialize()
        # TODO: assert something
        self.assertFalse(data['squashed'])
        self.assertTrue(squashed_data['squashed'])

    def test_vars(self):
        # vars as a dict.
        ds = {'environment': [],
              'vars': {'var_2_key': 'var_2_value',
                       'var_1_key': 'var_1_value'}}
        b = self._base_validate(ds)
        self.assertEquals(b.vars['var_1_key'], 'var_1_value')

    def test_vars_list_of_dicts(self):
        ds = {'environment': [],
              'vars': [{'var_2_key': 'var_2_value'},
                       {'var_1_key': 'var_1_value'}]
              }
        b = self._base_validate(ds)
        self.assertEquals(b.vars['var_1_key'], 'var_1_value')

    def test_vars_not_dict_or_list(self):
        ds = {'environment': [],
              'vars': 'I am a string, not a dict or a list of dicts'}
        self.assertRaises(AnsibleParserError, self.b.load_data, ds)

    def test_vars_not_valid_identifier(self):
        ds = {'environment': [],
              'vars': [{'var_2_key': 'var_2_value'},
                       {'1an-invalid identifer': 'var_1_value'}]
              }
        self.assertRaises(AnsibleParserError, self.b.load_data, ds)

    def test_vars_is_list_but_not_of_dicts(self):
        ds = {'environment': [],
              'vars': ['foo', 'bar', 'this is a string not a dict']
              }
        self.assertRaises(AnsibleParserError, self.b.load_data, ds)

    def test_vars_is_none(self):
        # If vars is None, we should get a empty dict back
        ds = {'environment': [],
              'vars': None
              }
        b = self._base_validate(ds)
        self.assertEquals(b.vars, {})

    def test_validate_empty(self):
        self.b.validate()
        self.assertTrue(self.b._validated)

    def test_getters(self):
        # not sure why these exist, but here are tests anyway
        loader = self.b.get_loader()
        variable_manager = self.b.get_variable_manager()
        self.assertEquals(loader, self.b._loader)
        self.assertEquals(variable_manager, self.b._variable_manager)


class TestExtendValue(unittest.TestCase):
    # _extend_value could be a module or staticmethod but since its
    # not, the test is here.
    def test_extend_value_list_newlist(self):
        b = base.Base()
        value_list = ['first', 'second']
        new_value_list = ['new_first', 'new_second']
        ret = b._extend_value(value_list, new_value_list)
        self.assertEquals(value_list + new_value_list, ret)

    def test_extend_value_list_newlist_prepend(self):
        b = base.Base()
        value_list = ['first', 'second']
        new_value_list = ['new_first', 'new_second']
        ret_prepend = b._extend_value(value_list, new_value_list, prepend=True)
        self.assertEquals(new_value_list + value_list, ret_prepend)

    def test_extend_value_newlist_list(self):
        b = base.Base()
        value_list = ['first', 'second']
        new_value_list = ['new_first', 'new_second']
        ret = b._extend_value(new_value_list, value_list)
        self.assertEquals(new_value_list + value_list, ret)

    def test_extend_value_newlist_list_prepend(self):
        b = base.Base()
        value_list = ['first', 'second']
        new_value_list = ['new_first', 'new_second']
        ret = b._extend_value(new_value_list, value_list, prepend=True)
        self.assertEquals(value_list + new_value_list, ret)

    def test_extend_value_string_newlist(self):
        b = base.Base()
        some_string = 'some string'
        new_value_list = ['new_first', 'new_second']
        ret = b._extend_value(some_string, new_value_list)
        self.assertEquals([some_string] + new_value_list, ret)

    def test_extend_value_string_newstring(self):
        b = base.Base()
        some_string = 'some string'
        new_value_string = 'this is the new values'
        ret = b._extend_value(some_string, new_value_string)
        self.assertEquals([some_string, new_value_string], ret)

    def test_extend_value_list_newstring(self):
        b = base.Base()
        value_list = ['first', 'second']
        new_value_string = 'this is the new values'
        ret = b._extend_value(value_list, new_value_string)
        self.assertEquals(value_list + [new_value_string], ret)

    def test_extend_value_none_none(self):
        b = base.Base()
        ret = b._extend_value(None, None)
        self.assertEquals(len(ret), 0)
        self.assertFalse(ret)

    def test_extend_value_none_list(self):
        b = base.Base()
        ret = b._extend_value(None, ['foo'])
        self.assertEquals(ret, ['foo'])


class ExampleException(Exception):
    pass


# naming fails me...
class ExampleParentBaseSubClass(base.Base):
    _test_attr_parent_string = FieldAttribute(isa='string', default='A string attr for a class that may be a parent for testing')

    def __init__(self):

        super(ExampleParentBaseSubClass, self).__init__()
        self._dep_chain = None

    def get_dep_chain(self):
        return self._dep_chain


class ExampleSubClass(base.Base):
    _test_attr_blip = FieldAttribute(isa='string', default='example sub class test_attr_blip',
                                     inherit=False,
                                     always_post_validate=True)

    def __init__(self):
        super(ExampleSubClass, self).__init__()

    def get_dep_chain(self):
        if self._parent:
            return self._parent.get_dep_chain()
        else:
            return None


class BaseSubClass(base.Base):
    _name = FieldAttribute(isa='string', default='', always_post_validate=True)
    _test_attr_bool = FieldAttribute(isa='bool', always_post_validate=True)
    _test_attr_int = FieldAttribute(isa='int', always_post_validate=True)
    _test_attr_float = FieldAttribute(isa='float', default=3.14159, always_post_validate=True)
    _test_attr_list = FieldAttribute(isa='list', listof=string_types, always_post_validate=True)
    _test_attr_list_no_listof = FieldAttribute(isa='list', always_post_validate=True)
    _test_attr_list_required = FieldAttribute(isa='list', listof=string_types, required=True,
                                              default=[], always_post_validate=True)
    _test_attr_barelist = FieldAttribute(isa='barelist', always_post_validate=True)
    _test_attr_string = FieldAttribute(isa='string', default='the_test_attr_string_default_value')
    _test_attr_string_required = FieldAttribute(isa='string', required=True,
                                                default='the_test_attr_string_default_value')
    _test_attr_percent = FieldAttribute(isa='percent', always_post_validate=True)
    _test_attr_set = FieldAttribute(isa='set', default=set(), always_post_validate=True)
    _test_attr_dict = FieldAttribute(isa='dict', default={'a_key': 'a_value'}, always_post_validate=True)
    _test_attr_class = FieldAttribute(isa='class', class_type=ExampleSubClass)
    _test_attr_class_post_validate = FieldAttribute(isa='class', class_type=ExampleSubClass,
                                                    always_post_validate=True)
    _test_attr_unknown_isa = FieldAttribute(isa='not_a_real_isa', always_post_validate=True)
    _test_attr_example = FieldAttribute(isa='string', default='the_default',
                                        always_post_validate=True)
    _test_attr_none = FieldAttribute(isa='string', always_post_validate=True)
    _test_attr_preprocess = FieldAttribute(isa='string', default='the default for preprocess')
    _test_attr_method = FieldAttribute(isa='string', default='some attr with a getter',
                                       always_post_validate=True)
    _test_attr_method_missing = FieldAttribute(isa='string', default='some attr with a missing getter',
                                               always_post_validate=True)

    def _preprocess_data_basesubclass(self, ds):
        return ds

    def preprocess_data(self, ds):
        return super(BaseSubClass, self).preprocess_data(ds)

    def _get_attr_test_attr_method(self):
        return 'foo bar'

    def _validate_test_attr_example(self, attr, name, value):
        if not isinstance(value, str):
            raise ExampleException('_test_attr_example is not a string: %s type=%s' % (value, type(value)))

    def _post_validate_test_attr_example(self, attr, value, templar):
        after_template_value = templar.template(value)
        return after_template_value

    def _post_validate_test_attr_none(self, attr, value, templar):
        return None

    def _get_parent_attribute(self, attr, extend=False, prepend=False):
        value = None
        try:
            value = self._attributes[attr]
            if self._parent and (value is None or extend):
                parent_value = getattr(self._parent, attr, None)
                if extend:
                    value = self._extend_value(value, parent_value, prepend)
                else:
                    value = parent_value
        except KeyError:
            pass

        return value


# terrible name, but it is a TestBase subclass for testing subclasses of Base
class TestBaseSubClass(TestBase):
    ClassUnderTest = BaseSubClass

    def _base_validate(self, ds):
        ds['test_attr_list_required'] = []
        return super(TestBaseSubClass, self)._base_validate(ds)

    def test_attr_bool(self):
        ds = {'test_attr_bool': True}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_bool, True)

    def test_attr_int(self):
        MOST_RANDOM_NUMBER = 37
        ds = {'test_attr_int': MOST_RANDOM_NUMBER}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_int, MOST_RANDOM_NUMBER)

    def test_attr_int_del(self):
        MOST_RANDOM_NUMBER = 37
        ds = {'test_attr_int': MOST_RANDOM_NUMBER}
        bsc = self._base_validate(ds)
        del bsc.test_attr_int
        self.assertNotIn('test_attr_int', bsc._attributes)

    def test_attr_float(self):
        roughly_pi = 4.0
        ds = {'test_attr_float': roughly_pi}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_float, roughly_pi)

    def test_attr_percent(self):
        percentage = '90%'
        percentage_float = 90.0
        ds = {'test_attr_percent': percentage}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_percent, percentage_float)

    # This method works hard and gives it its all and everything it's got. It doesn't
    # leave anything on the field. It deserves to pass. It has earned it.
    def test_attr_percent_110_percent(self):
        percentage = '110.11%'
        percentage_float = 110.11
        ds = {'test_attr_percent': percentage}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_percent, percentage_float)

    # This method is just here for the paycheck.
    def test_attr_percent_60_no_percent_sign(self):
        percentage = '60'
        percentage_float = 60.0
        ds = {'test_attr_percent': percentage}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_percent, percentage_float)

    def test_attr_set(self):
        test_set = set(['first_string_in_set', 'second_string_in_set'])
        ds = {'test_attr_set': test_set}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_set, test_set)

    def test_attr_set_string(self):
        test_data = ['something', 'other']
        test_value = ','.join(test_data)
        ds = {'test_attr_set': test_value}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_set, set(test_data))

    def test_attr_set_not_string_or_list(self):
        test_value = 37.1
        ds = {'test_attr_set': test_value}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_set, set([test_value]))

    def test_attr_dict(self):
        test_dict = {'a_different_key': 'a_different_value'}
        ds = {'test_attr_dict': test_dict}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_dict, test_dict)

    def test_attr_dict_string(self):
        test_value = 'just_some_random_string'
        ds = {'test_attr_dict': test_value}
        self.assertRaisesRegexp(AnsibleParserError, 'is not a dictionary', self._base_validate, ds)

    def test_attr_class(self):
        esc = ExampleSubClass()
        ds = {'test_attr_class': esc}
        bsc = self._base_validate(ds)
        self.assertIs(bsc.test_attr_class, esc)

    def test_attr_class_wrong_type(self):
        not_a_esc = ExampleSubClass
        ds = {'test_attr_class': not_a_esc}
        bsc = self._base_validate(ds)
        self.assertIs(bsc.test_attr_class, not_a_esc)

    def test_attr_class_post_validate(self):
        esc = ExampleSubClass()
        ds = {'test_attr_class_post_validate': esc}
        bsc = self._base_validate(ds)
        self.assertIs(bsc.test_attr_class_post_validate, esc)

    def test_attr_class_post_validate_class_not_instance(self):
        not_a_esc = ExampleSubClass
        ds = {'test_attr_class_post_validate': not_a_esc}
        self.assertRaisesRegexp(AnsibleParserError, 'is not a valid.*got a.*Meta.*instead',
                                self._base_validate, ds)

    def test_attr_class_post_validate_wrong_class(self):
        not_a_esc = 37
        ds = {'test_attr_class_post_validate': not_a_esc}
        self.assertRaisesRegexp(AnsibleParserError, 'is not a valid.*got a.*int.*instead',
                                self._base_validate, ds)

    def test_attr_remote_user(self):
        ds = {'remote_user': 'testuser'}
        bsc = self._base_validate(ds)
        # TODO: attemp to verify we called parent gettters etc
        self.assertEquals(bsc.remote_user, 'testuser')

    def test_attr_example_undefined(self):
        ds = {'test_attr_example': '{{ some_var_that_shouldnt_exist_to_test_omit }}'}
        exc_regex_str = 'test_attr_example.*has an invalid value, which includes an undefined variable.*some_var_that_shouldnt*'
        self.assertRaises(AnsibleParserError)

    def test_attr_name_undefined(self):
        ds = {'name': '{{ some_var_that_shouldnt_exist_to_test_omit }}'}
        bsc = self._base_validate(ds)
        # the attribute 'name' is special cases in post_validate
        self.assertEquals(bsc.name, '{{ some_var_that_shouldnt_exist_to_test_omit }}')

    def test_subclass_validate_method(self):
        ds = {'test_attr_list': ['string_list_item_1', 'string_list_item_2'],
              'test_attr_example': 'the_test_attr_example_value_string'}
        # Not throwing an exception here is the test
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_example, 'the_test_attr_example_value_string')

    def test_subclass_validate_method_invalid(self):
        ds = {'test_attr_example': [None]}
        self.assertRaises(ExampleException, self._base_validate, ds)

    def test_attr_none(self):
        ds = {'test_attr_none': 'foo'}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_none, None)

    def test_attr_string(self):
        the_string_value = "the new test_attr_string_value"
        ds = {'test_attr_string': the_string_value}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_string, the_string_value)

    def test_attr_string_invalid_list(self):
        ds = {'test_attr_string': ['The new test_attr_string', 'value, however in a list']}
        self.assertRaises(AnsibleParserError, self._base_validate, ds)

    def test_attr_string_required(self):
        the_string_value = "the new test_attr_string_required_value"
        ds = {'test_attr_string_required': the_string_value}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_string_required, the_string_value)

    def test_attr_list_invalid(self):
        ds = {'test_attr_list': {}}
        self.assertRaises(AnsibleParserError, self._base_validate, ds)

    def test_attr_list(self):
        string_list = ['foo', 'bar']
        ds = {'test_attr_list': string_list}
        bsc = self._base_validate(ds)
        self.assertEquals(string_list, bsc._attributes['test_attr_list'])

    def test_attr_list_none(self):
        ds = {'test_attr_list': None}
        bsc = self._base_validate(ds)
        self.assertEquals(None, bsc._attributes['test_attr_list'])

    def test_attr_list_no_listof(self):
        test_list = ['foo', 'bar', 123]
        ds = {'test_attr_list_no_listof': test_list}
        bsc = self._base_validate(ds)
        self.assertEquals(test_list, bsc._attributes['test_attr_list_no_listof'])

    def test_attr_list_required(self):
        string_list = ['foo', 'bar']
        ds = {'test_attr_list_required': string_list}
        bsc = self.ClassUnderTest()
        bsc.load_data(ds)
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        bsc.post_validate(templar)
        self.assertEquals(string_list, bsc._attributes['test_attr_list_required'])

    def test_attr_list_required_empty_string(self):
        string_list = [""]
        ds = {'test_attr_list_required': string_list}
        bsc = self.ClassUnderTest()
        bsc.load_data(ds)
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        self.assertRaisesRegexp(AnsibleParserError, 'cannot have empty values',
                                bsc.post_validate, templar)

    def test_attr_barelist(self):
        ds = {'test_attr_barelist': 'comma,separated,values'}
        bsc = self._base_validate(ds)
        self.assertEquals(['comma', 'separated', 'values'], bsc._attributes['test_attr_barelist'])

    def test_attr_unknown(self):
        a_list = ['some string']
        ds = {'test_attr_unknown_isa': a_list}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_unknown_isa, a_list)

    def test_attr_method(self):
        ds = {'test_attr_method': 'value from the ds'}
        bsc = self._base_validate(ds)
        # The value returned by the subclasses _get_attr_test_attr_method
        self.assertEquals(bsc.test_attr_method, 'foo bar')

    def test_attr_method_missing(self):
        a_string = 'The value set from the ds'
        ds = {'test_attr_method_missing': a_string}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_method_missing, a_string)
