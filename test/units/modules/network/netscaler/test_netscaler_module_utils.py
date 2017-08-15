
#  Copyright (c) 2017 Citrix Systems
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
#

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock


from ansible.module_utils.netscaler import ConfigProxy, get_immutables_intersection, ensure_feature_is_enabled, log, loglines


class TestNetscalerConfigProxy(unittest.TestCase):

    def test_values_copied_to_actual(self):
        actual = Mock()
        client = Mock()
        values = {
            'some_key': 'some_value',
        }
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['some_key']
        )
        self.assertEqual(actual.some_key, values['some_key'], msg='Failed to pass correct value from values dict')

    def test_none_values_not_copied_to_actual(self):
        actual = Mock()
        client = Mock()
        actual.key_for_none = 'initial'
        print('actual %s' % actual.key_for_none)
        values = {
            'key_for_none': None,
        }
        print('value %s' % actual.key_for_none)
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['key_for_none']
        )
        self.assertEqual(actual.key_for_none, 'initial')

    def test_missing_from_values_dict_not_copied_to_actual(self):
        actual = Mock()
        client = Mock()
        values = {
            'irrelevant_key': 'irrelevant_value',
        }
        print('value %s' % actual.key_for_none)
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['key_for_none']
        )
        print('none %s' % getattr(actual, 'key_for_none'))
        self.assertIsInstance(actual.key_for_none, Mock)

    def test_bool_yes_no_transform(self):
        actual = Mock()
        client = Mock()
        values = {
            'yes_key': True,
            'no_key': False,
        }
        transforms = {
            'yes_key': ['bool_yes_no'],
            'no_key': ['bool_yes_no']
        }
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['yes_key', 'no_key'],
            transforms=transforms,
        )
        actual_values = [actual.yes_key, actual.no_key]
        self.assertListEqual(actual_values, ['YES', 'NO'])

    def test_bool_on_off_transform(self):
        actual = Mock()
        client = Mock()
        values = {
            'on_key': True,
            'off_key': False,
        }
        transforms = {
            'on_key': ['bool_on_off'],
            'off_key': ['bool_on_off']
        }
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['on_key', 'off_key'],
            transforms=transforms,
        )
        actual_values = [actual.on_key, actual.off_key]
        self.assertListEqual(actual_values, ['ON', 'OFF'])

    def test_callable_transform(self):
        actual = Mock()
        client = Mock()
        values = {
            'transform_key': 'hello',
            'transform_chain': 'hello',
        }
        transforms = {
            'transform_key': [lambda v: v.upper()],
            'transform_chain': [lambda v: v.upper(), lambda v: v[:4]]
        }
        ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['transform_key', 'transform_chain'],
            transforms=transforms,
        )
        actual_values = [actual.transform_key, actual.transform_chain]
        self.assertListEqual(actual_values, ['HELLO', 'HELL'])


class TestNetscalerModuleUtils(unittest.TestCase):

    def test_immutables_intersection(self):
        actual = Mock()
        client = Mock()
        values = {
            'mutable_key': 'some value',
            'immutable_key': 'some other value',
        }
        proxy = ConfigProxy(
            actual=actual,
            client=client,
            attribute_values_dict=values,
            readwrite_attrs=['mutable_key', 'immutable_key'],
            immutable_attrs=['immutable_key'],
        )
        keys_to_check = ['mutable_key', 'immutable_key', 'non_existant_key']
        result = get_immutables_intersection(proxy, keys_to_check)
        self.assertListEqual(result, ['immutable_key'])

    def test_ensure_feature_is_enabled(self):
        client = Mock()
        attrs = {'get_enabled_features.return_value': ['GSLB']}
        client.configure_mock(**attrs)
        ensure_feature_is_enabled(client, 'GSLB')
        ensure_feature_is_enabled(client, 'LB')
        client.enable_features.assert_called_once_with('LB')

    def test_log_function(self):
        messages = [
            'First message',
            'Second message',
        ]
        log(messages[0])
        log(messages[1])
        self.assertListEqual(messages, loglines, msg='Log messages not recorded correctly')
