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

import os
import sys

import pytest

from units.compat import unittest
from ansible.plugins.filter.network import parse_xml, type5_pw, hash_salt, comp_type5, vlan_parser

from ansible.errors import AnsibleFilterError

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'network')

with open(os.path.join(fixture_path, 'show_vlans_xml_output.txt')) as f:
    output_xml = f.read()


class TestNetworkParseFilter(unittest.TestCase):

    @unittest.skipIf(sys.version_info[:2] == (2, 6), 'XPath expression not supported in this version')
    def test_parse_xml_to_list_of_dict(self):
        spec_file_path = os.path.join(fixture_path, 'show_vlans_xml_spec.yml')
        parsed = parse_xml(output_xml, spec_file_path)
        expected = {'vlans': [{'name': 'test-1', 'enabled': True, 'state': 'active', 'interface': None, 'vlan_id': 100, 'desc': None},
                              {'name': 'test-2', 'enabled': True, 'state': 'active', 'interface': None, 'vlan_id': None, 'desc': None},
                              {'name': 'test-3', 'enabled': True, 'state': 'active', 'interface': 'em3.0', 'vlan_id': 300, 'desc': 'test vlan-3'},
                              {'name': 'test-4', 'enabled': False, 'state': 'inactive', 'interface': None, 'vlan_id': 400, 'desc': 'test vlan-4'},
                              {'name': 'test-5', 'enabled': False, 'state': 'inactive', 'interface': 'em5.0', 'vlan_id': 500, 'desc': 'test vlan-5'}]}
        self.assertEqual(parsed, expected)

    @unittest.skipIf(sys.version_info[:2] == (2, 6), 'XPath expression not supported in this version')
    def test_parse_xml_to_dict(self):
        spec_file_path = os.path.join(fixture_path, 'show_vlans_xml_with_key_spec.yml')
        parsed = parse_xml(output_xml, spec_file_path)
        expected = {'vlans': {'test-4': {'name': 'test-4', 'enabled': False, 'state': 'inactive', 'interface': None, 'vlan_id': 400, 'desc': 'test vlan-4'},
                              'test-3': {'name': 'test-3', 'enabled': True, 'state': 'active', 'interface': 'em3.0', 'vlan_id': 300, 'desc': 'test vlan-3'},
                              'test-1': {'name': 'test-1', 'enabled': True, 'state': 'active', 'interface': None, 'vlan_id': 100, 'desc': None},
                              'test-5': {'name': 'test-5', 'enabled': False, 'state': 'inactive', 'interface': 'em5.0', 'vlan_id': 500, 'desc': 'test vlan-5'},
                              'test-2': {'name': 'test-2', 'enabled': True, 'state': 'active', 'interface': None, 'vlan_id': None, 'desc': None}}
                    }
        self.assertEqual(parsed, expected)

    @unittest.skipIf(sys.version_info[:2] == (2, 6), 'XPath expression not supported in this version')
    def test_parse_xml_with_condition_spec(self):
        spec_file_path = os.path.join(fixture_path, 'show_vlans_xml_with_condition_spec.yml')
        parsed = parse_xml(output_xml, spec_file_path)
        expected = {'vlans': [{'name': 'test-5', 'enabled': False, 'state': 'inactive', 'interface': 'em5.0', 'vlan_id': 500, 'desc': 'test vlan-5'}]}
        self.assertEqual(parsed, expected)

    def test_parse_xml_with_single_value_spec(self):
        spec_file_path = os.path.join(fixture_path, 'show_vlans_xml_single_value_spec.yml')
        parsed = parse_xml(output_xml, spec_file_path)
        expected = {'vlans': ['test-1', 'test-2', 'test-3', 'test-4', 'test-5']}
        self.assertEqual(parsed, expected)

    def test_parse_xml_validate_input(self):
        spec_file_path = os.path.join(fixture_path, 'show_vlans_xml_spec.yml')
        output = 10

        with self.assertRaises(Exception) as e:
            parse_xml(output_xml, 'junk_path')
        self.assertEqual("unable to locate parse_xml template: junk_path", str(e.exception))

        with self.assertRaises(Exception) as e:
            parse_xml(output, spec_file_path)
        self.assertEqual("parse_xml works on string input, but given input of : %s" % type(output), str(e.exception))


class TestNetworkType5(unittest.TestCase):

    def test_defined_salt_success(self):
        password = 'cisco'
        salt = 'nTc1'
        expected = '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        parsed = type5_pw(password, salt)
        self.assertEqual(parsed, expected)

    def test_undefined_salt_success(self):
        password = 'cisco'
        parsed = type5_pw(password)
        self.assertEqual(len(parsed), 30)

    def test_wrong_data_type(self):

        with self.assertRaises(Exception) as e:
            type5_pw([])
        self.assertEqual("type5_pw password input should be a string, but was given a input of list", str(e.exception))

        with self.assertRaises(Exception) as e:
            type5_pw({})
        self.assertEqual("type5_pw password input should be a string, but was given a input of dict", str(e.exception))

        with self.assertRaises(Exception) as e:
            type5_pw('pass', [])
        self.assertEqual("type5_pw salt input should be a string, but was given a input of list", str(e.exception))

        with self.assertRaises(Exception) as e:
            type5_pw('pass', {})
        self.assertEqual("type5_pw salt input should be a string, but was given a input of dict", str(e.exception))

    def test_bad_salt_char(self):

        with self.assertRaises(Exception) as e:
            type5_pw('password', '*()')
        self.assertEqual("type5_pw salt used inproper characters, must be one of "
                         "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./", str(e.exception))

        with self.assertRaises(Exception) as e:
            type5_pw('password', 'asd$')
        self.assertEqual("type5_pw salt used inproper characters, must be one of "
                         "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./", str(e.exception))


class TestHashSalt(unittest.TestCase):

    def test_retrieve_salt(self):
        password = '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        parsed = hash_salt(password)
        self.assertEqual(parsed, 'nTc1')

        password = '$2y$14$wHhBmAgOMZEld9iJtV.'
        parsed = hash_salt(password)
        self.assertEqual(parsed, '14')

    def test_unparseable_salt(self):
        password = '$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        with self.assertRaises(Exception) as e:
            parsed = hash_salt(password)
        self.assertEqual("Could not parse salt out password correctly from $nTc1$Z28sUTcWfXlvVe2x.3XAa.", str(e.exception))


class TestCompareType5(unittest.TestCase):

    def test_compare_type5_boolean(self):
        unencrypted_password = 'cisco'
        encrypted_password = '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        parsed = comp_type5(unencrypted_password, encrypted_password)
        self.assertEqual(parsed, True)

    def test_compare_type5_string(self):
        unencrypted_password = 'cisco'
        encrypted_password = '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        parsed = comp_type5(unencrypted_password, encrypted_password, True)
        self.assertEqual(parsed, '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.')

    def test_compate_type5_fail(self):
        unencrypted_password = 'invalid_password'
        encrypted_password = '$1$nTc1$Z28sUTcWfXlvVe2x.3XAa.'
        parsed = comp_type5(unencrypted_password, encrypted_password)
        self.assertEqual(parsed, False)


class TestVlanParser(unittest.TestCase):

    def test_compression(self):
        raw_list = [1, 2, 3]
        parsed_list = ['1-3']
        self.assertEqual(vlan_parser(raw_list), parsed_list)

    def test_single_line(self):
        raw_list = [100, 1688, 3002, 3003, 3004, 3005, 3102, 3103, 3104, 3105, 3802, 3900, 3998, 3999]
        parsed_list = ['100,1688,3002-3005,3102-3105,3802,3900,3998,3999']
        self.assertEqual(vlan_parser(raw_list), parsed_list)

    def test_multi_line(self):
        raw_list = [100, 1688, 3002, 3004, 3005, 3050, 3102, 3104, 3105, 3151, 3802, 3900, 3998, 3999]
        parsed_list = ['100,1688,3002,3004,3005,3050,3102,3104,3105,3151', '3802,3900,3998,3999']
        self.assertEqual(vlan_parser(raw_list), parsed_list)
