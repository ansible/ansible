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

from ansible.compat.tests import unittest
from ansible.plugins.filter.network import parse_xml

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
        self.assertEqual("unable to locate parse_cli template: junk_path", str(e.exception))

        with self.assertRaises(Exception) as e:
            parse_xml(output, spec_file_path)
        self.assertEqual("parse_xml works on string input, but given input of : %s" % type(output), str(e.exception))
