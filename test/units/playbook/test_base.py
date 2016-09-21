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

from ansible.compat.six import string_types
from ansible.errors import AnsibleParserError
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar
from ansible.playbook import base

from units.mock.loader import DictDataLoader


class TestBase(unittest.TestCase):
    def test(self):
        b = base.Base()
        self.assertIsInstance(b, base.Base)

    def test_dump(self):
        b = base.Base()
        ret = b.dump_me()
        print(ret)

    def test_copy(self):
        b = base.Base()
        copy = b.copy()
        print(copy)
        self.assertIsInstance(copy, base.Base)

    def test_serialize(self):
        b = base.Base()
        ret = b.serialize()
        print(ret)

    def test_serialize_then_deserialize(self):
        b = base.Base()
        copy = b.copy()
        ret = b.serialize()
        b.deserialize(ret)
        # TODO: not a great test, but coverage...
        self.assertDictEqual(b.serialize(), copy.serialize())

    def test_post_validate_empty(self):
        b = base.Base()
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        ret = b.post_validate(templar)
        self.assertIsNone(ret)

    def test_get_ds_none(self):
        b = base.Base()
        ds = b.get_ds()
        self.assertIsNone(ds)

    def test_load_data_ds_is_none(self):
        b = base.Base()
        self.assertRaises(AssertionError, b.load_data, None)

    def test_load_data_invalid_attr(self):
        b = base.Base()
        ds = {'not_a_valid_attr': [],
              'other': None}

        self.assertRaises(AnsibleParserError, b.load_data, ds)

    def test_load_data_invalid_attr_type(self):
        b = base.Base()
        ds = {'environment': True}

        # environment is supposed to be  a list. This
        # seems like it shouldn't work?
        ret = b.load_data(ds)
        self.assertEquals(True, ret._attributes['environment'])
        #self.assertRaises(AnsibleParserError, b.load_data, ds)

    def test_post_validate(self):
        b = base.Base()
        ds = {'environment': [],
              'port': 443}
        b.load_data(ds)

        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        b.post_validate(templar)

    def test_post_validate_invalid_attr_types(self):
        b = base.Base()
        ds = {'environment': [],
              'port': 'some_port'}
        b.load_data(ds)
        print(b._valid_attrs)
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        b.post_validate(templar)
        print(b._attributes['port'])

    def test_post_validate_templated(self):
        b = base.Base()
        ds = {'environment': [],
              'port': 443}

        b.load_data(ds)

        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        b.post_validate(templar)

    def test_squash(self):
        b = base.Base()
        data = b.serialize()
        b.squash()
        squashed_data = b.serialize()
        print(data)
        print(squashed_data)

    def test_validate_empty(self):
        b = base.Base()
        b.validate()

    def test_getters(self):
        b = base.Base()
        # not sure why these exist, but here are tests anyway
        loader = b.get_loader()
        variable_manager = b.get_variable_manager()
        self.assertEquals(loader, b._loader)
        self.assertEquals(variable_manager, b._variable_manager)


class ExampleException(Exception):
    pass


class ExampleSubClass(base.Base):
    _test_attr_blip = FieldAttribute(isa='string', default='example sub class test_attr_blip',
                                     inherit=False,
                                     always_post_validate=True)

    def __init__(self):
        super(ExampleSubClass, self).__init__()


class BaseSubClass(base.Base):
    _test_attr_bool = FieldAttribute(isa='bool', always_post_validate=True)
    _test_attr_int = FieldAttribute(isa='int', always_post_validate=True)
    _test_attr_float = FieldAttribute(isa='float', default=3.14159, always_post_validate=True)
    _test_attr_list = FieldAttribute(isa='list', listof=string_types, always_post_validate=True)
    _test_attr_list_no_listof = FieldAttribute(isa='list', always_post_validate=True)
    _test_attr_string = FieldAttribute(isa='string', default='the_test_attr_string_default_value')
    _test_attr_percent = FieldAttribute(isa='percent', always_post_validate=True)
    _test_attr_set = FieldAttribute(isa='set', default=set(), always_post_validate=True)
    _test_attr_dict = FieldAttribute(isa='dict', default={'a_key': 'a_value'}, always_post_validate=True)
    _test_attr_class = FieldAttribute(isa='class', class_type=ExampleSubClass)
    _test_attr_class_post_validate = FieldAttribute(isa='class', class_type=ExampleSubClass,
                                                    always_post_validate=True)

    _test_attr_example = FieldAttribute(isa='string', default='the_default',
                                        always_post_validate=True)
    _test_attr_preprocess = FieldAttribute(isa='string', default='the default for preprocess')
    _test_attr_list = FieldAttribute(isa='list', listof=string_types, always_post_validate=True)
#    _test_attr_omit = FieldAttribute(isa='string', always_post_validate=True)

    def _validate_test_attr_example(self, attr, name, value):
        # print("_validate_test_attr_example attr=%s name=%s value=%s" % (attr, name, value))
        # print('type(value)=%s instance(value,str)=%s' % (type(value), isinstance(value, str)))
        if not isinstance(value, str):
            raise ExampleException('_test_attr_example is not a string: %s type=%s' % (value, type(value)))

    def _post_validate_test_attr_example(self, attr, value, templar):
        # print("_post_validate_test_attr_example attr=%s value=%s templar=%s" % (attr, value, templar))
        after_template_value = templar.template(value)
        #print('_post_validate after_template_value=%s' % after_template_value)
        return after_template_value


class TestBaseSubClass(unittest.TestCase):
    def test_attr_bool(self):
        ds = {'test_attr_bool': True}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_bool, True)

    def _base_validate(self, ds):
        print('')
        bsc = BaseSubClass()
        bsc.load_data(ds)
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        bsc.post_validate(templar)
        return bsc

    def test_attr_int(self):
        MOST_RANDOM_NUMBER = 37
        ds = {'test_attr_int': MOST_RANDOM_NUMBER}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_int, MOST_RANDOM_NUMBER)

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

    def test_attr_dict(self):
        test_dict = {'a_different_key': 'a_different_value'}
        ds = {'test_attr_dict': test_dict}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_dict, test_dict)

    def test_attr_class(self):
        ds = {'test_attr_class': ExampleSubClass}
        bsc = self._base_validate(ds)
        self.assertIs(bsc.test_attr_class, ExampleSubClass)

    def test_attr_class_post_validate(self):
        ds = {'test_attr_class_post_validate': ExampleSubClass}
        bsc = self._base_validate(ds)
        self.assertIs(bsc.test_attr_class_post_validate, ExampleSubClass)

#    def test_attr_omit(self):
#        ds = {'test_attr_omit': '{{ some_var_that_shouldnt_exist_to_test_omit }}'}
#        bsc = self._base_validate(ds)
#        print('bsd=%s' % bsc)

    def test_subclass_validate_method(self):
        ds = {'test_attr_list': ['string_list_item_1', 'string_list_item_2'],
              'test_attr_example': 'the_test_attr_example_value_string'}
        ret = self._base_validate(ds)

    def test_subclass_validate_method_invalid(self):
        ds = {'test_attr_example': [None]}
        self.assertRaises(ExampleException, self._base_validate, ds)

    def test_attr_string(self):
        the_string_value = "the new test_attr_string_value"
        ds = {'test_attr_string': the_string_value}
        bsc = self._base_validate(ds)
        self.assertEquals(bsc.test_attr_string, the_string_value)

    def test_attr_string_invalid_list(self):
        ds = {'test_attr_string': ['The new test_attr_string', 'value, however in a list']}
        self.assertRaises(AnsibleParserError, self._base_validate, ds)

    def test_attr_list_invalid(self):
        ds = {'test_attr_list': {}}
        self.assertRaises(AnsibleParserError, self._base_validate, ds)

    def test_attr_list(self):
        string_list = ['foo', 'bar']
        ds = {'test_attr_list': string_list}
        bsc = self._base_validate(ds)
        self.assertEquals(string_list, bsc._attributes['test_attr_list'])

    def test_attr_list_no_listof(self):
        test_list = ['foo', 'bar', 123]
        ds = {'test_attr_list_no_listof': test_list}
        bsc = self._base_validate(ds)
        self.assertEquals(test_list, bsc._attributes['test_attr_list_no_listof'])
